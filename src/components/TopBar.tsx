import React, { useEffect, useMemo } from "react";
import { useHsStore } from "../store/store";
import { playSong } from "../utils/play";
import { Scatter } from "react-chartjs-2";
import { onSave, onLoad } from '../utils/file';
import 'chart.js/auto'

const TopBar: React.FC = () => {
  const { grid, parser, preamble, setPreamble, output, setOutput, songName, setSongName, setGrid, setSongUrl, songUrl } = useHsStore()

  const onPlay = () => {
    const { yValues, songUrl } = playSong(grid, parser, [preamble]);
    setOutput(yValues);
    setSongUrl(songUrl);
  }

  const chartOptions = {
    // responsive: true,
    plugins: {
      tooltip: {
        enabled: false
      }
    }
  };

  const chartData = useMemo(() => ({
    labels: output?.map((_, i) => i),
    datasets: [
      {
        label: 'Waveform',
        data: output,
        borderColor: 'rgba(0, 0, 0, 0.2)',
        backgroundColor: 'rgba(0, 0, 0, 0.1)',
        tension: 0.1,
      }
    ]
  }), [output]);

  return <div className="flex flex-col grow self-stretch place-items-center place-content-center">
    <div className="flex grow self-stretch place-items-center place-content-center">
      <h1 className="px-4 italic self-stretch place-items-center place-content-center flex flex-col" ><span className="leading-none text-2xl text-gray-500">IAOTECHSOFT</span><span className="leading-none font-bold text-3xl">HOLYSAW&trade;</span></h1>
      <textarea 
        value={preamble} 
        onChange={(e) => setPreamble(e.target.value)} 
        className="grow self-stretch"></textarea>
      <div className="flex flex-col self-stretch">
        <div className="flex place-items-center grow self-stretch">
          <label className="font-mono text-xs p-1 m-0">Name: </label>
          <input type='text' value={songName} onChange={(e) => setSongName(e.target.value)} className="grow text-xs" />
        </div>
        <div className="flex place-items-center grow self-stretch">
          <button className="grow self-stretch w-20" onClick={onSave(preamble, grid, songName, document)}>💾 Save .ihs</button>
          <button className="grow self-stretch w-20">
            <label htmlFor="file">📂 Load .ihs</label>
            <input type="file" id="file" onChange={onLoad(setPreamble, setSongName, setGrid)} className="hidden" />
          </button>
        </div>
        <div className="flex place-items-center grow self-stretch">
          <a className="grow self-stretch w-20 button place-content-center place-items-center flex" href={songUrl} download={`${songName}.wav`}>📥 Save .wav</a>
        </div>
      </div>
      <button 
        className="self-stretch text-2xl w-20"
        onClick={onPlay}
      >
        ▶️
      </button>
    </div>
    {false && output?.length > 0 && <div className="flex self-stretch rounded bg-blue-100 m-0.5">
      <Scatter options={chartOptions} datasetIdKey="waveform" data={chartData} />
    </div>}
  </div>;
};

export default TopBar;