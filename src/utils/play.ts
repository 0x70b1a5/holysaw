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

export const getFnsFromGrid = (grid: Grid) => {
    const fns: string[] = [];
    grid.forEach((second, secondIndex) => {
        let secondAsFn = `unlikelyFunctionNameForStepping${secondIndex}(x) = [`
        second.forEach((cell, cellIndex) => {
            if (!cell) return;
            try {
                console.log({ secondIndex, cellIndex, cell});
                secondAsFn += `${cell}, `;
            } catch (e) {
                console.log(e);
            }
        });
        secondAsFn += ']';
        secondAsFn = secondAsFn.replace(', ]', ']');
        fns.push(secondAsFn);
    });
    console.log(fns)
    return fns;
}

export const playSong = (song: Grid, parser: Parser, preambles: string[]) => {
    parser.clear();
    parser.evaluate(preambles.join('\n'));
    const fns = getFnsFromGrid(song);
    const SAMPLE_RATE = 44100;
    const MS_PER_SECOND = 1000;
    const yValues = [];
    let log = ''
    for (let row = 0; row < song.length; row++) {
        parser.evaluate(fns[row]);
        const rowMs = parser.get('rowMs');
        const rowSamples = rowMs * SAMPLE_RATE / MS_PER_SECOND;
        log += `${rowMs}ms, ${rowSamples} samples\n`
        for (let sample = 0; sample < rowSamples; sample++) {
            const x = row + sample / rowSamples;
            for (let fn = 0; fn <= row; fn++) {
                parser.evaluate(`unlikelyFunctionNameForStepping${fn}(${x})`);
            }
            const y = parser.get('y');
            yValues.push(y);
        }
    }
    console.log(log);

    const audioContext = new window.AudioContext();
    const audioBuffer = audioContext.createBuffer(1, yValues.length, SAMPLE_RATE);
    for (let sample = 0; sample < yValues.length; sample++) {
        audioBuffer.getChannelData(0)[sample] = yValues[sample];
    }

    // Convert the AudioBuffer to a .wav file
    const wav = toWav(audioBuffer);

    // Create a Blob from the .wav file
    const blob = new Blob([new DataView(wav)], { type: 'audio/wav' });

    // Create a URL from the Blob
    const url = window.URL.createObjectURL(blob);

    // Create and play an <audio> element with the URL as its source
    const audio = new Audio(url);
    window.document.body.appendChild(audio);
    audio.play();
}
