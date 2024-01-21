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

export const getRowsAsFns = (grid: Grid) => {
    const fns: string[] = [];
    grid.forEach((row, idx) => {
        let rowAsFn = `mathjsFnForRowNumber${idx}(x) = [`
        row.cells.forEach((cell, cellIndex) => {
            if (!cell) return;
            try {
                console.log({ secondIndex: idx, cellIndex, cell});
                rowAsFn += `${cell}, `;
            } catch (e) {
                console.log(e);
            }
        });
        rowAsFn += ']';
        rowAsFn = rowAsFn.replace(', ]', ']');
        fns.push(rowAsFn);
    });
    console.log(fns)
    return fns;
}

export const playSong = (song: Grid, parser: Parser, preambles: string[]) => {
    parser.clear();
    parser.evaluate(preambles.join('\n'));
    const rowsAsFns = getRowsAsFns(song);
    const SAMPLE_RATE = 44100;
    const MS_PER_SECOND = 1000;
    const yValues = [];
    let x = 0;
    let log = ''
    for (let rowIdx = 0; rowIdx < song.length; rowIdx++) {
        const row = song[rowIdx];
        parser.evaluate(rowsAsFns[rowIdx]);
        const rowSamples = row.msDuration * SAMPLE_RATE / MS_PER_SECOND;
        log += `row #${rowIdx}, ${row.msDuration}ms, ${rowSamples} samples\n`
        for (let sample = 0; sample < rowSamples; sample++) {
            for (let fn = 0; fn <= rowIdx; fn++) {
                parser.evaluate(`mathjsFnForRowNumber${fn}(${x})`);
            }
            const y = parser.evaluate('y()');
            log += `x: ${x}, y: ${y}\n`;
            yValues.push(y);
            x++;
        }
    }
    // download log as a text file
    // const logBlob = new Blob([log], { type: 'text/plain' });
    // const logUrl = window.URL.createObjectURL(logBlob);
    // const logAnchor = document.createElement('a');
    // logAnchor.href = logUrl;
    // logAnchor.download = 'log.txt';
    // logAnchor.click();

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

    return yValues
}
