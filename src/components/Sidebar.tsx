import React from "react";
import { useHsStore } from "../store/store";

interface SidebarProps {
  onPlay: (preambles: string[]) => void
}
const Sidebar: React.FC<SidebarProps> = ({ onPlay }) => {
  const { preambles, setPreambles, output, tickRate, setTickRate } = useHsStore()
  const [newPreamble, setNewPreamble] = React.useState<string>('')
  return <div className="w-48 bg-gray-200 border border-r-1 border-y-0 border-l-0 border-gray-300">
    <div className="p-2">HOLYSAW</div>
    <div className='p-2 flex flex-col'>
      <div className="p-2">Preambles</div>
      {preambles.map((preamble: string, index: number) => (
        <input key={index} type="text" value={preamble} onChange={(e) => {
          const newPreambles = [...preambles];
          newPreambles[index] = e.target.value;
          setPreambles(newPreambles);
        }} className="border border-gray-300 p-2 m-0 w-full" />
      ))}
      <input type="text" value={newPreamble} onChange={(e) => setNewPreamble(e.target.value)} className="border border-gray-300 p-2 m-0 w-full" />
    </div>
    <div className="p-2">
      <label className="p-2">
        Tick Rate
        <div className="text-xs">(1000 = 1 column/s)</div>
      </label>
      <input type="number" value={tickRate} className="border border-gray-300 p-2 m-0 w-full" onChange={(e) => setTickRate(Number(e.target.value))} />
    </div>
    <div className="p-2">
      <label className="p-2">Output</label>
      <textarea readOnly value={output} />
    </div>
    <div className="p-2">
      <button className="border border-gray-300 p-2 m-0 w-full bg-green-400" onClick={() => onPlay(preambles)}>Play</button>
    </div>
  </div>;
};

export default Sidebar;