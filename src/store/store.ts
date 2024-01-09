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
    preambles: string[]
    setPreambles: (preamble: string[]) => void
    output: string
    setOutput: (output: string) => void
    tickRate: number
    setTickRate: (tickRate: number) => void
    tuning: number
    setTuning: (tuning: number) => void
}

export const useHsStore = create<HsStore>()(
    (set, get) => ({
        get,
        set,
        tuning: 440,
        setTuning: (tuning: number) => set({ tuning }),
        tickRate: 1000,
        setTickRate: (tickRate: number) => set({ tickRate }),
        output: '',
        setOutput: (output: string) => set({ output }),
        grid: [
            ['', '', 'y=0'],
            ['', '', 'y=1'],
            ['', '', 'y=0'],
            ['', '', 'y=-1'], 
            ['', '', 'y=0'],
            ['', '', 'y=1'],
            ['', '', 'y=0'],
            ['', '', 'y=-1'], 
        ],
        setGrid: (newGrid: Grid) => set({ grid: newGrid }),
        timeIndex: 0,
        focusedRow: 0,
        setFocusedRow: (focusedRow: number) => set({ focusedRow }),
        setTimeIndex: (timeIndex: number) => set({ timeIndex }),
        parser: parser(),
        preambles: [],
        setPreambles: (preambles: string[]) => set({ preambles })
    })
);