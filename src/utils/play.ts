import Pizzicato from 'pizzicato';
import { Grid } from '../types/grid';
import { Parser, parser, sec } from 'mathjs';
import toWav from 'audiobuffer-to-wav'

export const playSequence = (baseFrequency: number, multipliers: number[]) => {
    // Create a sound with the base frequency
    let sineWave = new Pizzicato.Sound({ source: 'wave', options: { frequency: baseFrequency } });

    // Change the frequency and play the sound for each multiplier
    multipliers.forEach((multiplier, index) => {
        // Delay the frequency change and the start of the sound by 1 second times the index
        setTimeout(() => {
            sineWave.frequency = baseFrequency * multiplier;
        }, index * 1000);
    });
    sineWave.play();
    setTimeout(() => {
        sineWave.stop();
    }, multipliers.length * 1000);
}
const SAMPLE_RATE = 44100;

export const getValuesFromSong = (songMaster: Grid, parser: Parser, preamble: string, stopMs?: number) => {
    console.log('getValuesFromSong', songMaster, parser, preamble, stopMs)
    const song = [...songMaster]
    parser.clear();
    parser.evaluate(preamble);
    const yValues = [];
    let log = ''
    /* OLD CODE
    for (let rowIdx = 0; rowIdx < song.length; rowIdx++) {
        const row = song[rowIdx];
        const rowSamples = row.msDuration * SAMPLE_RATE / MS_PER_SECOND;
        log += `row #${rowIdx}, ${row.msDuration}ms, ${rowSamples} samples\n`
        for (let cellIdx = 0; cellIdx < row.cells.length; cellIdx++) {
            const cellValue = row.cells[cellIdx];
            if (!cellValue) {
                continue;
            }
            parser.evaluate(`${cellValue}`);
            console.log(`${cellValue}`)
        }
        for (let sample = 0; sample < rowSamples; sample++) {
            parser.evaluate(`x=${sample}`);
            const y = parser.evaluate('y()');
            log += `x: ${sample}, y: ${y}\n`;
            yValues.push(y);
        }
        
    }
    */
    // NEW CODE
    // The Grid is a list of Channels. Each Channel has a list of Cells. Each Cell has a duration and a content.
    // The duration is the number of milliseconds that the Cell should be played for.
    // The content is a string that should be evaluated by the mathjs parser.
    // The parser has a variable x that is set to the current sample number.
    // The parser has a function y() that returns the current sample value.
    // We need to evaluate the content of each Cell for the duration of the Cell.
    // Track the current sample, and for each Channel, determine which Cell is currently playing.
    // Run those Cells through the parser and add the result to the yValues array.
    // We need to evaluate all of the Cells at the current sample, so we need to loop through all of the Channels.
    let maxDurationMs = song.reduce((max, channel) => {
        return Math.max(max, channel.cells.reduce((acc, cell) => {
            return acc + cell.msDuration
        }, 0));
    }, 0)
    if (stopMs !== undefined && stopMs < maxDurationMs) {
        maxDurationMs = stopMs;
    }
    const totalSamples = maxDurationMs * 44.1 // 44.1 samples per millisecond
    for (let sample = 0; sample <= totalSamples; sample++) {
        if (sample % 1000 === 0) {
            console.log(`${sample} / ${totalSamples}`);
        }
        parser.evaluate(`x=${sample}`);
        for (let channelIndex = 0; channelIndex < song.length; channelIndex++) {
            const channel = song[channelIndex];
            if (channel.executed) {
                continue;
            }
            channel.executed = true;
            let cellIdx = 0;
            while (
                cellIdx < channel.cells.length && 
                (
                    // 44.1 * sum of msDuration up to now is less than sample
                    44.1 * channel.cells.slice(0, cellIdx).reduce((acc, cell) => acc + cell.msDuration, 0) < sample
                )
            ) {
                cellIdx++;
            }
            if (cellIdx < channel.cells.length) {
                const cell = channel.cells[cellIdx];
                if (cell.content) {
                    parser.evaluate(cell.content)
                    log += `${cell.content}\n`;
                }
            }
        }
        let y = 0
        y = parser.evaluate('y()');
        log += `x: ${sample}, y: ${y}\n`;
        yValues.push(y);
    }
    song.forEach(channel => channel.executed = false)
    return { yValues, log };
}

interface PlayOptions {
    song: Grid, 
    name: string,
    parser: Parser, 
    preamble: string, 
    playAudio: boolean
    saveAsWav: boolean
    audioContext: AudioContext
    setAnalyserNode: (analyserNode: AnalyserNode) => void
}
export const playSong = ({ song: songMaster, name, parser, preamble, playAudio, saveAsWav, audioContext, setAnalyserNode }: PlayOptions) => {
    const { yValues, log } = getValuesFromSong(songMaster, parser, preamble)

    const audioBuffer = audioContext.createBuffer(1, yValues.length, SAMPLE_RATE);
    audioBuffer.copyToChannel(new Float32Array(yValues), 0);

    let url = ''

    if (saveAsWav) {
        url = bufferAsWave(audioBuffer);
        const a = document.createElement('a');
        a.href = url;
        a.download = name+'.wav';
        a.click();
    }

    if (playAudio) {
        const source = audioContext.createBufferSource();
        source.buffer = audioBuffer;
        const analyserNode = audioContext.createAnalyser();
        analyserNode.fftSize = 256;
        setAnalyserNode(analyserNode);
        
        const bufferLength = analyserNode.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        analyserNode.getByteTimeDomainData(dataArray);

        source.connect(audioContext.destination);
        source.connect(analyserNode);
        source.onended = () => {
            source.disconnect(audioContext.destination);
            source.disconnect(analyserNode);
        }
        source.start();
    }

    const logBlob = new Blob([log], { type: 'text/plain' });
    const logUrl = window.URL.createObjectURL(logBlob);

    return { yValues, songUrl: url, logUrl }
}

export const bufferAsWave = (audioBuffer: AudioBuffer) => {

    // Convert the AudioBuffer to a .wav file
    const wav = toWav(audioBuffer);

    // Create a Blob from the .wav file
    const blob = new Blob([new DataView(wav)], { type: 'audio/wav' });

    // Create a URL from the Blob
    const url = window.URL.createObjectURL(blob);

    return url;
}