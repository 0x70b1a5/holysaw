import React from 'react';

import { useHsStore } from './store/store';
import { playSong } from './utils/play';
import TopBar from './components/TopBar';
import TextCell from './components/TextCell';
import ExpandoBox from './components/ExpandoBox';

// Main App component
function App() {
  const { grid, setGrid, timeIndex, setTimeIndex, focusedRow, setFocusedRow, } = useHsStore()

  const addCellToRows = () => {
    const newGrid = grid.map(row => [...row, '']);
    setGrid(newGrid);
  };

  const addRow = () => {
    const newGrid = [...grid, grid[0].map(() => '')];
    setGrid(newGrid);
  }

  return (
    <div className="flex-col w-screen" id='main'>
      <TopBar />
      <div className='flex grow self-stretch'>
        <div className='flex flex-col grow self-stretch overflow-y-auto' id='container'>
          {grid.map((row, rindex) => (
            <div key={rindex} className="flex grow border border-b-1 border-t-0 border-x-0 border-solid">
              <ExpandoBox>
                {String(rindex).padStart(3, '0')}
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
            className='p-2 m-0 hover:bg-blue-200 bg-blue-100'
          >+</button>
        </div> {/* container */}
        <button 
          onClick={addCellToRows} 
          className='p-2 m-0 hover:bg-blue-200 bg-blue-100'
        >+</button>
      </div>
    </div> // main
  );
}

export default App;
