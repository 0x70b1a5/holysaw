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

export const getValuesFromGrid = (grid: Grid, parser: Parser) => {
    const values: number[] = [];
    grid.forEach((row, rowIndex) => {
        parser.evaluate(`x=${rowIndex}`);
        row.forEach((cell, cellIndex) => {
            if (!cell) return;
            try {
                console.log({ rowIndex, cellIndex, cell});
                parser.evaluate(cell);
            } catch (e) {
                console.log(e);
            }
        });
        values.push(parser.get('y'))
    });
    console.log(values)
    return values;
}

export const generateValues = (grid: Grid, parser: Parser, preambles: string[]) => {
    parser.clear();
    parser.evaluate(preambles.join('\n'));
    const values = getValuesFromGrid(grid, parser);
    return values;
}

export const playValues = (song: Grid) => {
    let lengthOfSoundInSeconds = song.length;
    const SAMPLE_RATE = 44100;
    // Assuming `values` is your array of values between -1 and 1
    const audioContext = new window.AudioContext();
    console.log({ lengthOfSoundInSeconds })
    const audioBuffer = audioContext.createBuffer(1, lengthOfSoundInSeconds * SAMPLE_RATE, SAMPLE_RATE);
    const math = parser();

    // Fill the AudioBuffer with y values
    for (let secondsIndex = 0; secondsIndex < lengthOfSoundInSeconds - 1; secondsIndex++) {
        // math.evaluate(`x = ${secondsIndex}`);
        // song[secondsIndex].forEach((cell, cellIndex) => {
        //     if (!cell) return;
        //     try {
        //         math.evaluate(cell);
        //     } catch (e) {
        //         console.log(e);
        //     }
        // })

        math.evaluate('y(x) = sin(x)'); // replace with your actual expression
        math.evaluate(`x = ${secondsIndex}:${secondsIndex + SAMPLE_RATE}`);
        let yValues = math.evaluate(`map(x, y)`).toArray();
        console.log({ yValues })

        for (let sample = 0; sample < SAMPLE_RATE; sample++) {
            //     math.evaluate(`x = (${secondsIndex} + ${samples} / ${SAMPLE_RATE})`);
            //     const y = math.get('y');
            // console.log(yValues[sample - 1])
            audioBuffer.getChannelData(0)[secondsIndex * SAMPLE_RATE + sample] = yValues[sample - 1];
        }
        // console.log({ buffer: audioBuffer.getChannelData(0), secondsIndex,  })
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
