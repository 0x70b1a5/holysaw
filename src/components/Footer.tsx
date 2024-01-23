import { useHsStore } from "../store/store";

interface Props {
    scrollerRef: React.RefObject<HTMLDivElement>
}

export const Footer: React.FC<Props> = ({ scrollerRef }) => {
    const { grid, setGrid, defaultRowMs, setDefaultRowMs, } = useHsStore()

    const addRow = (e: any, rows?: number) => {

        const newGrid = [...grid];
        for (let i = 0; i < (rows ?? 1); i++) {
        newGrid.push({ msDuration: defaultRowMs, cells: Array(grid[0].cells.length).fill('') });
        }
        setGrid(newGrid);
        setTimeout(() => {
        scrollerRef.current?.scrollTo({ top: scrollerRef.current?.scrollHeight });
        }, 0);
    }
    
    return (
        <div className='flex place-items-center place-content-center text-xs'>
            <input 
                type="number" 
                value={defaultRowMs} 
                onChange={(e) => {
                    const val = e.currentTarget.value
                    if (val && parseInt(val) > 0) {
                        setDefaultRowMs(parseInt(val))
                    }
                }} 
                className="text-xs w-16 px-1 py-0.5" 
            />
            <span className='mr-4'>ms</span>
            <button 
                onClick={addRow} 
                className='self-center'
            >+1</button>
            <button 
                onClick={(e) => addRow(e, 10)} 
                className='self-center'
            >+10</button>
            <button 
                onClick={(e) => addRow(e, 100)} 
                className='self-center'
            >+100</button>
        </div>

    )
}