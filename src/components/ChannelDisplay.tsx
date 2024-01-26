import { playSong } from "../utils/play";
import ExpandoBox from "./ExpandoBox";
import TextCell from "./TextCell";
import { Cell, Channel } from "../types/grid";
import { useHsStore } from "../store/store";
import { ChannelFooter } from "./ChannelFooter";

interface Props {
    channel: Channel
    channelIndex: number
    scrollRef: React.RefObject<HTMLDivElement>
}
export const ChannelDisplay: React.FC<Props> = ({ channel, channelIndex, scrollRef }) => {
    const { grid, setGrid, focusedChannel, setFocusedChannel } = useHsStore()
    
    const msToClockTime = (channelIndex: number, upToCellIndex: number) => {
        const channel = grid[channelIndex];
        const msAfter = channel.cells.slice(0, upToCellIndex + 1).reduce((acc, cell) => acc + cell.msDuration, 0);
        const minutesAfter = Math.floor(msAfter / 60000);
        const secondsAfter = Math.floor((msAfter % 60000) / 1000);
        const millisecondsAfter = Math.floor(msAfter % 1000);
        return `${minutesAfter}:${secondsAfter.toString().padStart(2, '0')}.${millisecondsAfter.toString().padStart(3, '0')}`;
    }
  
    const msToSample = (upToCellIndex: number) => {
        const channel = grid[channelIndex];
        return Math.round(channel.cells.slice(0, upToCellIndex + 1).reduce((acc, cell) => acc + cell.msDuration, 0) * 44.1);
    }

    const onDeleteChannel = () => {
        if (window.confirm('Are you sure you want to delete this channel?')) {
            const newGrid = [...grid];
            newGrid.splice(channelIndex, 1);
            setGrid(newGrid);
        }
    };

    const onDeleteCell = (cindex: number) => {
        if (window.confirm('Are you sure you want to delete this cell?')) {
            const newGrid = [...grid];
            newGrid[channelIndex].cells.splice(cindex, 1);
            setGrid(newGrid);
        }
    }
    
    return (
        <div 
            key={channelIndex} 
            className="flex flex-col grow self-stretch"
        >
            {/* <ExpandoBox className='text-xs'>
                <div className='flex flex-col place-items-center'>
                    <span>x={msToSample(rindex)}</span>
                    <span className='text-gray-400'>{msToClockTime(rindex - 1)}</span>
                    <span className='text-gray-400'>{msToClockTime(rindex)}</span>
                </div>
            </ExpandoBox> */}
            {channel.cells.map((cell, cellIndex) => (
                <TextCell
                    key={cellIndex}
                    active={cellIndex === focusedChannel}
                    text={cell.content}
                    onChange={(text) => {
                        const newGrid = [...grid];
                        newGrid[channelIndex].cells = [...newGrid[channelIndex].cells]; // Create a copy of the row
                        newGrid[channelIndex].cells[cellIndex].content = text;
                        console.log({ channelIndex, cellIndex, text, grid })
                        setGrid(newGrid);
                    }}
                    channelIndex={channelIndex}
                    cellIndex={cellIndex}
                    placeholder={`x=${msToSample(cellIndex)}\n>${msToClockTime(channelIndex, cellIndex)}\n<${msToClockTime(channelIndex, cellIndex + 1)}`}
                    onFocus={() => { setFocusedChannel(cellIndex) }}
                />
            ))}
            {/* 

            OLD CODE
            <div className='flex flex-col self-stretch'>
                <div className='flex grow'>
                    <button 
                        onClick={addCellToRows} 
                        className='grow text-xs px-1 py-0.5 self-stretch bg-gray-100 hover:bg-gray-200'
                    >+</button>
                    <button 
                        onClick={onDeleteRow}
                        className='grow text-xs px-1 py-0.5 self-stretch bg-red-100 hover:bg-red-200'
                    >&times;</button>
                </div>
                <div className='flex grow'>
                    <button 
                        onClick={() => {
                            const gridUpToThisRow = grid.slice(0, rindex + 1);
                            playSong({ 
                                song: gridUpToThisRow, 
                                name: 'Untitled', 
                                parser, 
                                preamble, 
                                playAudio: true, 
                                saveAsWav: false,
                                audioContext,
                                setAnalyserNode
                            })
                        }}
                        className='grow text-xs px-1 py-0.5 self-stretch'
                    >▶️</button>
                </div>
            </div>
            
            */}
            <ChannelFooter channel={channel} scrollerRef={scrollRef} />
        </div>
    )
}

export default ChannelDisplay