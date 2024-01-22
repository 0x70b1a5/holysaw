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
      } catch (e) {
        alert('Error parsing file');
        return;
      }
      setPreamble(data.preamble);
      setSongName(data.songName);
      setGrid(data.grid);
    }
    reader.readAsText(file);
  }
}