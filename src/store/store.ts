import { create } from 'zustand';
import { Grid, GridRow } from '../types/grid';
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
    output: number[]
    setOutput: (output: number[]) => void
    defaultRowMs: number
    setDefaultRowMs: (defaultRowMs: number) => void
    songName: string
    setSongName: (songName: string) => void
}

export const useHsStore = create<HsStore>()(
    (set, get) => ({
        get,
        set,
        songName: 'my-song',
        setSongName: (songName: string) => set({ songName }),
        output: [],
        defaultRowMs: 1000,
        setDefaultRowMs: (defaultRowMs: number) => set({ defaultRowMs }),
        setOutput: (output: number[]) => set({ output }),
        grid: [
            { msDuration: 10, cells: ['y() = sin(tone*2*pi*x/sampleRate)', '', ''] },
            { msDuration: 10, cells: ['', '', ''] },
            { msDuration: 10, cells: ['', '', ''] },
            { msDuration: 10, cells: ['', '', ''] },
            { msDuration: 10, cells: ['', '', ''] },
            { msDuration: 10, cells: ['', '', ''] },
            { msDuration: 10, cells: ['', '', ''] },
            { msDuration: 10, cells: ['', '', ''] },
        ],
        setGrid: (newGrid: Grid) => set({ grid: newGrid }),
        timeIndex: 0,
        focusedRow: 0,
        setFocusedRow: (focusedRow: number) => set({ focusedRow }),
        setTimeIndex: (timeIndex: number) => set({ timeIndex }),
        parser: parser(),
        preamble: `tone = 440\nsampleRate = 44100\n`,
        setPreamble: (preamble: string) => set({ preamble })
    })
);