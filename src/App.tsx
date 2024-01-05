import React from 'react';

import { useHsStore } from './store/store';
import classNames from 'classnames';
import { concatenateValues, getValuesFromGrid } from './utils/play';

// Sidebar component
const Sidebar = () => {
  return <div className="w-48 bg-gray-200 border border-r-1 border-y-0 border-l-0 border-gray-300">
    <div className="p-2">HOLYSAW</div>
    <div className="p-2">
      <button className="border border-gray-300 p-2 m-0 w-full bg-green-400">Play</button>
    </div>
  </div>;
};

// Text cell component
interface TextCellProps {
  text: string;
  onChange: (text: string) => void;
  readonly?: boolean
  active?: boolean
  onFocus?: () => void
}
const TextCell: React.FC<TextCellProps> = ({ text, onChange, readonly, active, onFocus }) => {
  return (
    <input
      type="text"
      value={text}
      onChange={(e) => onChange(e.target.value)}
      onFocus={onFocus}
      className={classNames("border border-gray-300 p-2 m-0 w-16 border-l-0 border-t-0", { 'bg-gray-200': readonly, 'bg-gray-400': active })}
      readOnly={readonly}
    />
  );
};

// Main App component
function App() {
  const { parser, grid, setGrid, timeIndex, setTimeIndex, focusedRow, setFocusedRow } = useHsStore()

  const addCellToRows = () => {
    const newGrid = grid.map(row => [...row, '']);
    setGrid(newGrid);
  };

  const addRow = () => {
    const newGrid = [...grid, grid[0].map(() => '')];
    setGrid(newGrid);
  }

  return (
    <div className="flex" id='main'>
      <Sidebar />
      <div className="flex flex-col" id='container'>
        <div className="flex" id='top-bar'>
          <TextCell
            text=""
            onChange={() => {}}
            readonly />
          {grid[0].map((_, index) => (
            <TextCell
              key={index}
              active={index === timeIndex}
              text={String(index + 1)}
              onChange={() => {}}
              readonly
            />
          ))}
          
          <button onClick={addCellToRows} className='border border-gray-300 border-t-0 border-l-0 p-2 m-0 w-16'>+</button>
        </div>
        {grid.map((row, rindex) => (
          <div key={rindex} className="flex">
            <TextCell
              text={String.fromCharCode(65 + rindex)}
              onChange={() => {}}
              readonly
            />
            {row.map((cell, cindex) => (
              <TextCell
                key={cindex}
                active={cindex === timeIndex || rindex === focusedRow}
                text={cell}
                onChange={(text) => {
                  const newGrid = [...grid];
                  newGrid[rindex] = [...newGrid[rindex]]; // Create a copy of the row
                  newGrid[rindex][cindex] = text;
                  console.log({ rindex, cindex, text, grid })
                  setGrid(newGrid);
                }}
                onFocus={() => { setTimeIndex(cindex); setFocusedRow(rindex) }}
              />
            ))}
          </div>
        ))}
        <button onClick={addRow} className='border border-gray-300 border-t-0 border-l-0 p-2 m-0 w-16'>+</button>
        <div className="flex whitespace-pre font-mono" id='grid-display'>
          {concatenateValues(getValuesFromGrid(grid, parser))}
        </div>
      </div> {/* container */}
    </div> // main
  );
}

export default App;
