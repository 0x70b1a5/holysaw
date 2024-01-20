import { create } from 'zustand';
import { Grid } from '../types/grid';
import { Parser, parser } from 'mathjs';

export interface HsStore {
    grid: Grid,
    get: () => HsStore,
    set: (partial: HsStore | Partial<HsStore>) => void
    setGrid: (newGrid: Grid) => void
    timeIndex: number
    focusedRow: number
    setFocusedRow: (newFocusedRow: number) => void
    setTimeIndex: (newTimeIndex: number) => void
    parser: Parser
    preamble: string
    setPreamble: (preamble: string) => void
    output: string
    setOutput: (output: string) => void
}

export const useHsStore = create<HsStore>()(
    (set, get) => ({
        get,
        set,
        output: '',
        setOutput: (output: string) => set({ output }),
        grid: [
            ['', '', 'y=sin(440*2*pi*x)'],
            ['', '', ''],
            ['', '', ''],
            ['', '', ''], 
            ['', '', ''],
            ['', '', ''],
            ['', '', ''],
            ['', '', ''], 
        ],
        setGrid: (newGrid: Grid) => set({ grid: newGrid }),
        timeIndex: 0,
        focusedRow: 0,
        setFocusedRow: (focusedRow: number) => set({ focusedRow }),
        setTimeIndex: (timeIndex: number) => set({ timeIndex }),
        parser: parser(),
        preamble: `rowMs = 1000\ntone = 440`,
        setPreamble: (preamble: string) => set({ preamble })
    })
);