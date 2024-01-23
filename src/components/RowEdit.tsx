import { parser } from "mathjs";
import { playSong } from "../utils/play";
import ExpandoBox from "./ExpandoBox";
import TextCell from "./TextCell";
import { Cell, GridRow } from "../types/grid";
import { useHsStore } from "../store/store";

interface Props {
    row: GridRow
    rindex: number
}
export const EditRow: React.FC<Props> = ({ row, rindex }) => {
    const { grid, setGrid, timeIndex, setTimeIndex, focusedRow, setFocusedRow, parser, defaultRowMs, setDefaultRowMs, preamble, audioContext, setAnalyserNode } = useHsStore()
    
    const msToClockTime = (upToRowIndex: number) => {
      const msAfter = grid.slice(0, upToRowIndex + 1).reduce((acc, row) => acc + row.msDuration, 0);
      const minutesAfter = Math.floor(msAfter / 60000);
      const secondsAfter = Math.floor((msAfter % 60000) / 1000);
      const millisecondsAfter = Math.floor(msAfter % 1000);
      return `${minutesAfter}:${secondsAfter.toString().padStart(2, '0')}.${millisecondsAfter.toString().padStart(3, '0')}`;
    }
  
    const msToSample = (upToRowIndex: number) => {
      return Math.round(grid.slice(0, upToRowIndex + 1).reduce((acc, row) => acc + row.msDuration, 0) * 44100 / 1000);
    }

    const addCellToRows = () => {
        const newGrid = grid.map((row) => ({ ...row, cells: [...row.cells, '']}));
        setGrid(newGrid);
    };

    const onDeleteRow = () => {
        if (window.confirm('Are you sure you want to delete this row?')) {
        const newGrid = [...grid];
        newGrid.splice(rindex, 1);
        setGrid(newGrid);
        }
    };
    
    return (
        <div key={rindex} className="flex grow">
            <ExpandoBox className='text-xs'>
                <div className='flex flex-col place-items-center'>
                    <span>x={msToSample(rindex)}</span>
                    <span className='text-gray-400'>{msToClockTime(rindex - 1)}</span>
                    <span className='text-gray-400'>{msToClockTime(rindex)}</span>
                </div>
            </ExpandoBox>
            <TextCell
                text={row.msDuration.toString()}
                onChange={(text) => {
                    const newGrid = [...grid];
                    newGrid[rindex] = { ...newGrid[rindex], msDuration: parseInt(text) };
                    setGrid(newGrid);
                }}
                onFocus={() => { setTimeIndex(-1); setFocusedRow(rindex) }}
                placeholder='ms'
                className='grow-0'
            />
            {row.cells.map((cell, cindex) => (
                <TextCell
                    key={cindex}
                    active={cindex === timeIndex || rindex === focusedRow}
                    text={cell}
                    placeholder={`x=${msToSample(rindex)}`}
                    onChange={(text) => {
                        const newGrid = [...grid];
                        newGrid[rindex].cells = [...newGrid[rindex].cells]; // Create a copy of the row
                        newGrid[rindex].cells[cindex] = text;
                        console.log({ rindex, cindex, text, grid })
                        setGrid(newGrid);
                    }}
                    onFocus={() => { setTimeIndex(cindex); setFocusedRow(rindex) }}
                />
            ))}
            <div className='flex flex-col self-stretch'>
                <div className='flex grow'>
                    <button 
                        onClick={addCellToRows} 
                        className='grow text-xs px-1 py-0.5 self-stretch bg-gray-100 hover:bg-gray-200'
                    >+</button>
                    <button 
                        onClick={onDeleteRow}
                        className='grow text-xs px-1 py-0.5 self-stretch bg-red-100 hover:bg-red-200'
                    >&times;</button>
                </div>
                <div className='flex grow'>
                    <button 
                        onClick={() => {
                            const gridUpToThisRow = grid.slice(0, rindex + 1);
                            playSong({ 
                            song: gridUpToThisRow, 
                            name: 'Untitled', 
                            parser, 
                            preamble, 
                            playAudio: true, 
                            saveAsWav: false,
                            audioContext,
                            setAnalyserNode
                            })
                        }}
                        className='grow text-xs px-1 py-0.5 self-stretch'
                    >▶️</button>
                </div>
            </div>
        </div>
    )
}

export default EditRow