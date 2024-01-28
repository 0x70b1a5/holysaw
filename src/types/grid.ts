export type Cell = { 
    msDuration: number, 
    content: string
};
export type Grid = Channel[];
export type Channel = {
    cells: Cell[]
    executed?: boolean
};