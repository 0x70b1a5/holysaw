import React from 'react';

import { useHsStore } from './store/store';
import { playSong } from './utils/play';
import TopBar from './components/TopBar';
import TextCell from './components/TextCell';
import ExpandoBox from './components/ExpandoBox';

// Main App component
function App() {
  const { grid, setGrid, timeIndex, setTimeIndex, focusedRow, setFocusedRow, defaultRowMs } = useHsStore()

  const addCellToRows = () => {
    const newGrid = grid.map((row) => ({ ...row, cells: [...row.cells, '']}));
    setGrid(newGrid);
  };

  const addRow = () => {
    const newGrid = [...grid, { msDuration: defaultRowMs, cells: Array(grid[0].cells.length).fill('') }];
    setGrid(newGrid);
  }

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

  return (
    <div className="flex-col w-screen" id='main'>
      <TopBar />
      <div className='flex'>
        <div className='flex flex-col grow' id='container'>
          {grid.map((row, rindex) => (
            <div key={rindex} className="flex grow">
              <ExpandoBox className='text-xs'>
                <div className='flex'>
                  <button 
                    onClick={() => {
                      if (window.confirm('Are you sure you want to delete this row?')) {
                        const newGrid = [...grid];
                        newGrid.splice(rindex, 1);
                        setGrid(newGrid);
                      }
                    }}
                    className='text-[8px] px-1 mr-1 ml-[-4px] m-0 bg-transparent hover:bg-red-200 place-self-center'
                  >-</button>
                  <div className='flex flex-col place-items-center'>
                    <span>x={msToSample(rindex)}</span>
                    <span className='text-gray-400'>{msToClockTime(rindex - 1)}</span>
                    <span className='text-gray-400'>{msToClockTime(rindex)}</span>
                  </div>
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
                  placeholder={`x=${rindex}`}
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
            </div>
          ))}
          <button 
            onClick={addRow} 
            className='self-center'
          >+</button>
        </div> {/* container */}
        <button 
          onClick={addCellToRows} 
          className='self-center'
        >+</button>
      </div>
    </div> // main
  );
}

export default App;
