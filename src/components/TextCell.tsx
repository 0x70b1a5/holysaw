import classNames from "classnames";
import React, { useEffect } from "react";
import { useHsStore } from "../store/store";
import { getValuesFromSong } from "../utils/play";
interface TextCellProps {
  text: string;
  onChange: (text: string) => void;
  readonly?: boolean
  active?: boolean
  onFocus?: () => void
  placeholder?: string
  className?: string
  cellIndex?: number
  channelIndex?: number
}
const TextCell: React.FC<TextCellProps> = ({ text, onChange, readonly, active,onFocus, placeholder, className, cellIndex, channelIndex }) => {
  const { grid, setGrid, preamble, plays, parser } = useHsStore()
  const [expanded, setExpanded] = React.useState(false)
  const [variableReadout, setVariableReadout] = React.useState('')

  const focusChannelAndRow = (ch: number, row: number) => {
    const channel = document.getElementById(`cell-${row}-${ch}`);
    if (channel) {
      channel.focus();
    }
  }
  const onkeyup = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (cellIndex === undefined) return;
    if (channelIndex === undefined) return;

    // SHIFT-TAB: PREV CHANNEL
    if (e.key === 'Tab' && e.shiftKey) {
      e.preventDefault();
      if (cellIndex === 0 && channelIndex > 0) {
        focusChannelAndRow(channelIndex - 1, grid[channelIndex - 1].cells.length - 1);
      } else {
        focusChannelAndRow(channelIndex, cellIndex - 1);
      }
    }
    // TAB: NEXT CHANNEL
    else if (e.key === 'Tab') {
      e.preventDefault();
      if (cellIndex === grid[channelIndex].cells.length - 1 && channelIndex < grid.length - 1) {
        focusChannelAndRow(channelIndex + 1, 0);
      } else {
        focusChannelAndRow(channelIndex, cellIndex + 1);
      }
    }
    // // SHIFT-ENTER: PREV CELL
    // if (e.key === 'Enter' && e.shiftKey) {
    //   e.preventDefault();
    //   if (cellIndex === 0 && channelIndex > 0) {
    //     focusChannelAndRow(channelIndex - 1, grid[channelIndex - 1].cells.length - 1);
    //   } else {
    //     focusChannelAndRow(channelIndex, cellIndex - 1);
    //   }
    // }
    // // ENTER: NEXT CELL
    // else if (e.key === 'Enter') {
    //   e.preventDefault();
    //   if (cellIndex === grid[channelIndex].cells.length - 1 && channelIndex < grid.length - 1) {
    //     focusChannelAndRow(channelIndex + 1, 0);
    //   } else {
    //     focusChannelAndRow(channelIndex, cellIndex + 1);
    //   }
    // }
  }

  const addCellBelow = () => {
    if (channelIndex === undefined) return;
    if (cellIndex === undefined) return;
    const newGrid = [...grid];
    newGrid[channelIndex].cells = [...newGrid[channelIndex].cells];
    newGrid[channelIndex].cells.splice(cellIndex + 1, 0, { content: '', msDuration: newGrid[channelIndex].cells[cellIndex].msDuration });
    setGrid(newGrid);
  }

  const deleteCell = () => {
    if (channelIndex === undefined) return;
    if (cellIndex === undefined) return;
    if (window.confirm('Are you sure you want to delete this cell?')) {
      const newGrid = [...grid];
      newGrid[channelIndex].cells = [...newGrid[channelIndex].cells];
      newGrid[channelIndex].cells.splice(cellIndex, 1);
      setGrid(newGrid);
    }
  }

  useEffect(() => {
    if (channelIndex === undefined || cellIndex === undefined || !expanded) return;
    try {
      const msAtEndOfThisCell = grid[channelIndex].cells.slice(0, cellIndex + 1).reduce((acc, cell) => acc + cell.msDuration, 0);
      console.log({ channelIndex, cellIndex, text })
      const { yValues, log } = getValuesFromSong(grid, parser, preamble, msAtEndOfThisCell);
      setVariableReadout(JSON.stringify({...parser.getAll(), msAtEndOfThisCell}, null, 2))
    } catch (e) {
      console.error( 'Error: ' + JSON.stringify(e))
    }
  }, [text, plays])

  return (<div className="relative flex flex-col">
    <textarea
      id={`cell-${channelIndex}-${cellIndex}`}
      value={text}
      onChange={(e) => onChange(e.target.value)}
      onFocus={onFocus}
      className={classNames("grow self-stretch shrink-0", { 'bg-gray-200': readonly, 'bg-gray-100': active }, className)}
      readOnly={readonly}
      placeholder={placeholder}
      onKeyDown={onkeyup}
    ></textarea>
    {(channelIndex !== undefined && cellIndex !== undefined) && <div className="flex absolute top-0 right-0">
      <input
        className="text-xs px-1 py-0.5 bg-gray-100 hover:bg-gray-200 w-10 mr-1"
        value={grid[channelIndex].cells[cellIndex].msDuration}
        onChange={(e) => {
          const val = e.currentTarget.value
          if (val && parseInt(val) > 0) {
            const newGrid = [...grid];
            newGrid[channelIndex].cells = [...newGrid[channelIndex].cells];
            newGrid[channelIndex].cells[cellIndex].msDuration = parseInt(val);
            setGrid(newGrid);
          }
        }}
      />
      <button
        onClick={() => setExpanded(!expanded)}
        className='text-xs px-1 py-0.5 bg-gray-100 hover:bg-gray-200 mr-1'
      >...</button>
      <button
        onClick={addCellBelow}
        className='text-xs px-1 py-0.5 bg-gray-100 hover:bg-green-200 mr-1'
      >+</button>
      <button
        onClick={deleteCell}
        className='text-xs px-1 py-0.5 bg-gray-100 hover:bg-red-200 mr-1'
      >&times;</button>
    </div>}
    {expanded && <textarea 
      className="grow self-stretch bg-gradient-to-bl from-gray-100 to-gray-200"
      value={variableReadout}
      readOnly
    ></textarea>}
  </div>);
};

export default TextCell;