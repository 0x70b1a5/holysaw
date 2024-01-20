import React from 'react';

import { useHsStore } from './store/store';
import { playSong } from './utils/play';
import Sidebar from './components/Sidebar';
import TextCell from './components/TextCell';
import ExpandoBox from './components/ExpandoBox';

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
    <div className="flex w-screen h-screen" id='main'>
      <Sidebar onPlay={(preambles) => {
        playSong(grid, parser, preambles)
      }} />
      <div className='flex flex-col grow align-self-stretch overflow-y-auto' id='container'>
        {grid.map((row, rindex) => (
          <div key={rindex} className="flex grow align-self-stretch">
            <ExpandoBox>
              {rindex}
            </ExpandoBox>
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
        <button 
          onClick={addRow} 
          className='align-self-stretch p-2 m-0 hover:bg-gray-200'
        >+</button>
      </div> {/* container */}
      <button 
        onClick={addCellToRows} 
        className='p-2 m-0 hover:bg-gray-200'
      >+</button>
    </div> // main
  );
}

export default App;
