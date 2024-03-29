import { Grid } from "../types/grid";

export const onSave = (preamble: string, grid: Grid, songName: string, document: Document) => {
  return (e: React.MouseEvent<HTMLButtonElement, MouseEvent>) => {
    const data = JSON.stringify({ preamble, grid, songName }, undefined, 4);
    const blob = new Blob([data], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = songName+'.ihs';
    a.click();
  }
}

export const onLoad = (setPreamble: (preamble: string) => void, setSongName: (songName: string) => void, setGrid: (grid: Grid) => void) => {
  return (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target?.result as string;
      let data: any;
      try {
        data = JSON.parse(text);
        if (!data.preamble || !data.grid || !data.songName) {
          throw new Error('Missing preamble, grid, or songName');
        }
        if (!data.grid.length) {
          throw new Error('Grid must have at least one row');
        }
        if (!data.grid[0].cells.length) {
          throw new Error('Grid must have at least one cell');
        }
        // validate grid type
        const cell = data.grid[0].cells[0];
        if (!cell.msDuration || !cell.content) {
          throw new Error('Grid cell must have msDuration and content');
        }
      } catch (e: any) {
        alert('Error parsing file: ' + e.message);
        return;
      }
      setPreamble(data.preamble);
      setSongName(data.songName);
      setGrid(data.grid);
    }
    reader.readAsText(file);
  }
}