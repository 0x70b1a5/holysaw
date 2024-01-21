import React, { useEffect, useMemo } from "react";
import { useHsStore } from "../store/store";
import { playSong } from "../utils/play";
import { Scatter } from "react-chartjs-2";
import 'chart.js/auto'

const TopBar: React.FC = () => {
  const { grid, parser, preamble, setPreamble, output, setOutput, songName, setSongName, setGrid } = useHsStore()

  const onPlay = () => {
    const yVals = playSong(grid, parser, [preamble]);
    setOutput(yVals);
  }

  const onSave = () => {
    const data = JSON.stringify({ preamble, grid, songName });
    const blob = new Blob([data], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = songName+'.ihs';
    a.click();
  }

  const onLoad = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target?.result as string;
      let data: any;
      try {
        data = JSON.parse(text);
      } catch (e) {
        alert('Error parsing file');
        return;
      }
      setPreamble(data.preamble);
      setSongName(data.songName);
      setGrid(data.grid);
    }
    reader.readAsText(file);
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
      <h1 className="px-4 text-4xl font-bold italic self-stretch place-items-center place-content-center flex">HOLYSAW&trade;</h1>
      <textarea 
        value={preamble} 
        onChange={(e) => setPreamble(e.target.value)} 
        className="grow self-stretch"></textarea>
      <div className="flex flex-col">
        <div className="flex place-items-center">
          <label className="font-mono text-xs p-1 m-0">Name: </label>
          <input type='text' value={songName} onChange={(e) => setSongName(e.target.value)} className="text-xs" />
        </div>
        <div className="flex place-items-center grow">
          <button className="grow self-stretch text-2xl w-20" onClick={onSave}>💾</button>
          <button className="grow self-stretch text-2xl w-20">
            <label htmlFor="file">📂</label>
            <input type="file" id="file" onChange={onLoad} className="hidden" />
          </button>
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