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
}

export const useHsStore = create<HsStore>()(
    (set, get) => ({
    get,
    set,
    grid: Array(8).fill(Array(8).fill('').slice()).slice(),
    setGrid: (newGrid: Grid) => set({ grid: newGrid }),
    timeIndex: 0,
    focusedRow: 0,
    setFocusedRow: (focusedRow: number) => set({ focusedRow }),
    setTimeIndex: (timeIndex: number) => set({ timeIndex }),
    parser: parser()
    })
);