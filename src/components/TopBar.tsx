import React, { useEffect, useMemo, useRef } from "react";
import { useHsStore } from "../store/store";
import { playSong } from "../utils/play";
import { onSave, onLoad } from '../utils/file';
import classNames from "classnames";
import Waveform from "./Waveform";
import {createWorkerFactory, useWorker} from '@shopify/react-web-worker';
const createWorker = createWorkerFactory(() => import('../worker/worker'));

const TopBar: React.FC = () => {
  const { grid, parser, preamble, setPreamble, output, setOutput, songName, setSongName, setGrid, setSongUrl, songUrl, logUrl, setLogUrl, audioContext, setAnalyserNode } = useHsStore()
  const worker = useWorker(createWorker);

  const pixiRef = useRef<HTMLDivElement>(null);

  const onPlay = () => {
    const { yValues, songUrl, logUrl } = playSong({ 
      song: grid, 
      name: songName, 
      parser,
      preamble, 
      playAudio: true, 
      saveAsWav: false,
      audioContext, setAnalyserNode
    });
    setOutput(yValues);
    setSongUrl(songUrl);
    setLogUrl(logUrl);
  }

  return <div className="flex flex-col self-stretch place-items-center place-content-center">
    <div className="flex grow self-stretch place-items-center place-content-center">
      <h1 className="px-4 italic self-stretch place-items-center place-content-center flex flex-col" >
        <span className="leading-none text-2xl text-gray-500">IAOTECHSOFT</span>
        <span className="leading-none font-bold text-3xl">HOLYSAW&trade;</span>
      </h1>
      <textarea 
        value={preamble} 
        onChange={(e) => setPreamble(e.target.value)} 
        className="grow self-stretch"></textarea>
      <div className="flex grow m-0.5 bg-green-100 rounded self-stretch">
        <Waveform pref={pixiRef} />
      </div>
      <div className="flex flex-col self-stretch text-xs">
        <div className="flex place-items-center grow self-stretch">
          <label className="font-mono p-1 m-0">Name: </label>
          <input type='text' value={songName} onChange={(e) => setSongName(e.target.value)} className="grow" />
        </div>
        <div className="flex place-items-center grow self-stretch">
          <button className="grow self-stretch w-20" onClick={onSave(preamble, grid, songName, document)}>💾 Save .ihs</button>
          <button className="grow self-stretch w-20 relative">
            <label htmlFor="file" className="absolute top-0 bottom-0 left-0 right-0 cursor-pointer"></label>
            <input type="file" id="file" onChange={onLoad(setPreamble, setSongName, setGrid)} className="hidden" />
            <span>📂 Load .ihs</span>
          </button>
        </div>
        <div className="flex place-items-center grow self-stretch">
          <button
            className={classNames("grow self-stretch w-20")}
            onClick={() => playSong({ 
              song: grid, 
              name: songName,
              parser, 
              preamble,
              playAudio: false, 
              saveAsWav: true, 
              audioContext, 
              setAnalyserNode
            })}
          >
            📻 Save .wav  
          </button>
          <a
            className={classNames("grow self-stretch w-20 button place-content-center place-items-center flex", { 'disabled pointer-events-none bg-gray-200': !logUrl })}
            href={logUrl}
            download={`${songName}.log`}
          >
            📝 Save .log  
          </a>
        </div>
      </div>
      <button 
        className="self-stretch text-2xl w-20"
        onClick={onPlay}
      >
        ▶️
      </button>
    </div>
  </div>;
};

export default TopBar;