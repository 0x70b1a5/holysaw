export type Cell = string;
export type Grid = GridRow[];
export type GridRow = {
    msDuration: number, 
    cells: Cell[]
};