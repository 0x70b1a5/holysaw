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
export const playSong = ({ song, name, parser, preamble, playAudio, saveAsWav, audioContext, setAnalyserNode }: PlayOptions) => {
    parser.clear();
    parser.evaluate(preamble);
    const SAMPLE_RATE = 44100;
    const MS_PER_SECOND = 1000;
    const yValues = [];
    let log = ''
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