import React, { useEffect, useMemo, useRef } from "react";
import { useHsStore } from "../store/store";
import * as PIXI from 'pixi.js';

interface Props {
    pref: React.RefObject<HTMLDivElement> | null
}
const Waveform: React.FC<Props> = ({ pref }) => {
    const { output, pixiApp, analyserNode } = useHsStore()

    useEffect(() => {
        if (output && pref?.current && analyserNode) {
            if (pref.current.innerHTML == '') {
                pref.current.appendChild(pixiApp.view);
            }
            pixiApp.renderer.clear()
            pixiApp.resizeTo = pref.current;
            pixiApp.resize();

            const graphics = new PIXI.Graphics();
            const bufferLength = analyserNode.frequencyBinCount;
            const dataArray = new Uint8Array(bufferLength);
            pixiApp.stage.addChild(graphics as any);

            pixiApp.ticker.add(() => {
                analyserNode.getByteTimeDomainData(dataArray);
                graphics.clear();
                graphics.lineStyle(1, 0x000000, 1);
                graphics.moveTo(0, 50);
                for (let i = 0; i < bufferLength; i++) {
                    if (dataArray[i] == 128) continue;
                    // canvas height: 100px
                    const y = (dataArray[i] / 255) * 80;
                    // canvas width: determined by pixiAppRef.current
                    const x = (i / bufferLength) * (pref?.current?.clientWidth || 1);
                    graphics.lineTo(x, y);
                }
                pixiApp.renderer.render(pixiApp.stage);
            })
        }
    }, [output]);

    return <div className="flex grow w-20 max-h-[128px] m-0 bg-gradient-to-br from-green-100 to-white" ref={pref}></div>;
};

export default Waveform