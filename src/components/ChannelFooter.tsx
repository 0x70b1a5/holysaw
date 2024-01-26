import { useState } from "react";
import { useHsStore } from "../store/store";
import { Channel } from "../types/grid";

interface Props {
    scrollerRef: React.RefObject<HTMLDivElement>
    channel: Channel
}

export const ChannelFooter: React.FC<Props> = ({ scrollerRef, channel }) => {
    const { grid, setGrid, defaultRowMs, } = useHsStore()
    const [ms, setMs] = useState(defaultRowMs)

    const addCells = (e: any, numCells?: number) => {
        for (let i = 0; i < (numCells ?? 1); i++) {
            channel.cells.push({ content: '', msDuration: ms });
        }
        setGrid([...grid]);
        setTimeout(() => {
            scrollerRef.current?.scrollTo({ top: scrollerRef.current?.scrollHeight });
        }, 0);
    }
    
    return (
        <div className='flex flex-col place-items-center place-content-center text-xs'>
            <div className="flex">
                <input 
                    type="number" 
                    value={ms} 
                    onChange={(e) => {
                        const val = e.currentTarget.value
                        if (val && parseInt(val) > 0) {
                            setMs(parseInt(val))
                        }
                    }} 
                    className="text-xs w-16 px-1 py-0.5" 
                />
                <span className='mr-4'>ms</span>
            </div>
            <div className="flex">
                <button 
                    onClick={addCells} 
                    className='self-center'
                >+1</button>
                <button 
                    onClick={(e) => addCells(e, 10)} 
                    className='self-center'
                >+10</button>
                <button 
                    onClick={(e) => addCells(e, 100)} 
                    className='self-center'
                >+100</button>
            </div>
        </div>

    )
}