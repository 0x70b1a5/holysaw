import Pizzicato from 'pizzicato';
import { Grid } from '../types/grid';
import { Parser } from 'mathjs';

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
    const values: number[][] = [];
    grid.forEach((row, rowIndex) => {
        values.push([]);
        row.forEach((cell, cellIndex) => {
            let value = NaN;
            try {
                value = parser.evaluate(cell);
            } catch (e) {
                console.log(e);
            }
            values[rowIndex].push(value);
        });
    });
    return values;
}

export const concatenateValues = (values: number[][]) => {
    // left-pad each value with spaces so that they are all the same length
    const paddedValues: string[][] = [];
    values.forEach((row, rowIndex) => {
        paddedValues.push([]);
        row.forEach((cell, cellIndex) => {
            if (!cell) {
                paddedValues[rowIndex].push('     ');
                return;
            }
            paddedValues[rowIndex].push(cell.toString().slice(0, 4).padStart(5, ' '));
        });
    });
    // display the values
    return values.map(value => value.join(' ')).join('\n');
}