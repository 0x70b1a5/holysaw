import classNames from "classnames";
import React from "react";
import { useHsStore } from "../store/store";
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
const TextCell: React.FC<TextCellProps> = ({ text, onChange, readonly, active, onFocus, placeholder, className, cellIndex, channelIndex }) => {
  const { grid, setGrid } = useHsStore()
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
    // SHIFT-ENTER: PREV CELL
    if (e.key === 'Enter' && e.shiftKey) {
      e.preventDefault();
      if (cellIndex === 0 && channelIndex > 0) {
        focusChannelAndRow(channelIndex - 1, grid[channelIndex - 1].cells.length - 1);
      } else {
        focusChannelAndRow(channelIndex, cellIndex - 1);
      }
    }
    // ENTER: NEXT CELL
    else if (e.key === 'Enter') {
      e.preventDefault();
      if (cellIndex === grid[channelIndex].cells.length - 1 && channelIndex < grid.length - 1) {
        focusChannelAndRow(channelIndex + 1, 0);
      } else {
        focusChannelAndRow(channelIndex, cellIndex + 1);
      }
    }
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

  return (<div className="relative flex">
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
    {(channelIndex !== undefined && cellIndex !== undefined) && <>
      <input
        className="absolute text-xs px-1 py-0.5 bg-gray-100 hover:bg-gray-200 right-8 w-10 top-0"
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
        onClick={addCellBelow}
        className='absolute text-xs px-1 py-0.5 bg-gray-100 hover:bg-green-200 right-4 top-0'
      >+</button>
      <button
        onClick={deleteCell}
        className='absolute text-xs px-1 py-0.5 bg-gray-100 hover:bg-red-200 right-0 top-0'
      >&times;</button>
    </>}
  </div>);
};

export default TextCell;