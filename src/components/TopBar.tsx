import React from "react";
import { useHsStore } from "../store/store";
import { playSong } from "../utils/play";

const TopBar: React.FC = () => {
  const { grid, parser, preamble, setPreamble, output, } = useHsStore()

  const onPlay = () => {
    playSong(grid, parser, [preamble]);
  }

  return <div className="flex grow self-stretch place-items-center place-content-center">
    <div className="px-4 text-4xl font-bold italic bg-green-100 self-stretch place-items-center place-content-center flex">HOLYSAW&trade;</div>
    <textarea 
      value={preamble} 
      onChange={(e) => setPreamble(e.target.value)} 
      className="font-mono p-2 m-0 grow"></textarea>
    <button 
      className="px-2 py-1 m-0 bg-green-400 self-stretch text-2xl w-20 hover:bg-green-500"
      onClick={onPlay}
    >
      ▶️
    </button>
  </div>;
};

export default TopBar;