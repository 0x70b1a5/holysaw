import React, { useRef } from 'react';

import { useHsStore } from './store/store';
import TopBar from './components/TopBar';
import RowEdit from './components/RowEdit';
import { Footer } from './components/Footer';

// Main App component
function App() {
  const scrollerRef = useRef<HTMLDivElement>(null);

  const { grid, } = useHsStore()

  return (
    <div className="w-screen h-screen max-h-screen flex flex-col" id='main'>
      <TopBar />
      <div className='flex flex-col overflow-hidden' id='container'>
        <div className='flex flex-col overflow-y-auto h-full' ref={scrollerRef}>
          {grid.map((row, rindex) => <RowEdit key={rindex} row={row} rindex={rindex} />)}
        </div>
        <Footer scrollerRef={scrollerRef} />
      </div> {/* container */}
    </div> // main
  );
}

export default App;
