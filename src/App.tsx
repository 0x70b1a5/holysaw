import React from 'react';

import { useHsStore } from './store/store';
import { playSong } from './utils/play';
import Sidebar from './components/Sidebar';
import TextCell from './components/TextCell';

// Main App component
function App() {
  const { parser, grid, setGrid, timeIndex, setTimeIndex, focusedRow, setFocusedRow, output, setOutput, tickRate } = useHsStore()

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
      <Sidebar onPlay={(preambles) => {
        playSong(grid, parser, preambles)
      }} />
      <div className="flex flex" id='container'>
        <div className="flex flex-col" id='left-bar'>
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
          <div key={rindex} className="flex flex-col">
            <TextCell
              text={`${rindex}`}
              onChange={() => {}}
              readonly
            />
            {row.map((cell, cindex) => (
              <TextCell
                key={cindex}
                active={cindex === timeIndex || rindex === focusedRow}
                text={cell}
                placeholder={`x=${rindex}`}
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
      </div> {/* container */}
    </div> // main
  );
}

export default App;
