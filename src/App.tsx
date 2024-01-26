import React, { useRef } from 'react';

import { useHsStore } from './store/store';
import TopBar from './components/TopBar';
import ChannelDisplay from './components/ChannelDisplay';

// Main App component
function App() {
  const scrollerRef = useRef<HTMLDivElement>(null);

  const { grid, setGrid, defaultRowMs } = useHsStore()

  const addChannel = () => {
    const newGrid = [...grid]
    newGrid.push({ cells: [{ content: '', msDuration: defaultRowMs }] });
    setGrid(newGrid);
  }

  return (
    <div className="w-screen h-screen max-h-screen flex flex-col" id='main'>
      <TopBar />
      <div className='flex flex-col overflow-hidden max-w-screen' id='container'>
        <div className='flex overflow-y-auto h-full' ref={scrollerRef}>
          {grid.map((channel, channelIndex) => <ChannelDisplay key={channelIndex} channel={channel} channelIndex={channelIndex} scrollRef={scrollerRef} />)}
          <div className='flex flex-col place-items-center place-content-center text-xs'>
            <button onClick={addChannel} className='self-center'>+</button>
          </div>
        </div>
      </div> {/* container */}
    </div> // main
  );
}

export default App;
