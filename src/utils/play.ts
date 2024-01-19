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
    let lengthOfSoundInSeconds = song.length;
    const SAMPLE_RATE = 44100;
    const lengthOfSoundInSamples = lengthOfSoundInSeconds * SAMPLE_RATE;
    const audioContext = new window.AudioContext();
    // TODO: tickRate should be a variable
    const audioBuffer = audioContext.createBuffer(1, lengthOfSoundInSamples, SAMPLE_RATE);
    // Fill the AudioBuffer with y values
    let log = ``
    for (let secondsIndex = 0; secondsIndex < lengthOfSoundInSeconds; secondsIndex++) {
        log += `secondsIndex: ${secondsIndex}\n`
        let fnForThisSecond = fns[secondsIndex];
        log += `fnForThisSecond: ${fnForThisSecond}\n`
        parser.evaluate(fnForThisSecond);
        for (let sample = secondsIndex * SAMPLE_RATE; sample < secondsIndex * SAMPLE_RATE + SAMPLE_RATE; sample++) {
            const x = sample / SAMPLE_RATE;
            for (let fn = 0; fn <= secondsIndex; fn++) {
                parser.evaluate(`unlikelyFunctionNameForStepping${fn}(${x})`);
            }
            const y = parser.get('y');
            log += `x: ${x}, y: ${y}\n`
            // debugger;
            audioBuffer.getChannelData(0)[sample] = y;
        }
    }
    console.log(log);

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
