import { create } from 'zustand';
import { Grid, GridRow } from '../types/grid';
import { Parser, parser } from 'mathjs';
import * as PIXI from 'pixi.js';
import pixiApp from '../waveform/pixi';

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
    songUrl: string
    setSongUrl: (songUrl: string) => void
    logUrl: string
    setLogUrl: (logUrl: string) => void
    pixiApp: PIXI.Application<HTMLCanvasElement>
    setPixiApp: (pixiApp: PIXI.Application<HTMLCanvasElement>) => void
    audioContext: AudioContext
    setAudioContext: (audioContext: AudioContext) => void
    analyserNode: AnalyserNode | null
    setAnalyserNode: (analyserNode: AnalyserNode) => void
}

export const useHsStore = create<HsStore>()(
    (set, get) => ({
        get,
        set,
        audioContext: new AudioContext(),
        setAudioContext: (audioContext: AudioContext) => set({ audioContext }),
        analyserNode: null,
        setAnalyserNode: (analyserNode: AnalyserNode) => set({ analyserNode }),
        pixiApp: pixiApp,
        setPixiApp: (pixiApp: PIXI.Application<HTMLCanvasElement>) => set({ pixiApp }),
        songUrl: '',
        setSongUrl: (songUrl: string) => set({ songUrl }),
        logUrl: '',
        setLogUrl: (logUrl: string) => set({ logUrl }),
        songName: 'my-song',
        setSongName: (songName: string) => set({ songName }),
        output: [],
        defaultRowMs: 1000,
        setDefaultRowMs: (defaultRowMs: number) => set({ defaultRowMs }),
        setOutput: (output: number[]) => set({ output }),
        grid: [
            { msDuration: 10, cells: ['y() = sin(tone*tau*x/sampleRate)', '', ''] },
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