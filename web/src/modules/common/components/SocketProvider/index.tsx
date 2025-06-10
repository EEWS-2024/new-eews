'use client';

import {useEffect, useRef} from "react";
import {configKey} from "@/modules/common/configs";
import {useWaveFormStore} from "@/modules/waveForm/stores";
import {
    EpicWaveFormResponseInterface,
    PhasePickingResponseInterface,
    WaveFormResponseInterface
} from "@/modules/waveForm/stores/interface";
import {useSearchParams} from "next/navigation";

export default function SocketProvider({ children }: { children: React.ReactNode }) {
    const searchParams = useSearchParams()
    const stationCode = searchParams.get('stationCode');
    const ws = useRef<WebSocket | null>(null);
    const {setWaveForms, resetWaveForms, setPhasePicking, resetPhasePicking, setEpic, resetEpic} = useWaveFormStore()

    useEffect(() => {
        resetWaveForms()
        resetPhasePicking()
    }, [resetPhasePicking, resetWaveForms, stationCode]);

    useEffect(() => {
        resetEpic();

        const interval = setInterval(() => {
            resetEpic();
        }, 10 * 60 * 1000);

        return () => clearInterval(interval);
    }, [resetEpic]);

    useEffect(() => {
        const url = configKey.serverUrl.replace('http', 'ws');

        ws.current = new WebSocket(`${url}/ws?stationCode=${stationCode}`); // replace with your URL

        ws.current.onopen = () => {
            console.log('WebSocket connected');
        };

        ws.current.onmessage = (event) => {
            const message = JSON.parse(event.data);
            if (message.type === 'trace') {
                setWaveForms(message.payload as WaveFormResponseInterface, message.station as string)
            }
            if (message.type === 'phase_picking') {
                setPhasePicking(message.payload as PhasePickingResponseInterface)
            }
            if (message.type === 'epic_waveform') {
                setEpic(message.payload as EpicWaveFormResponseInterface)
            }
        };

        ws.current.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

        ws.current.onclose = () => {
            console.log('WebSocket disconnected');
        };

        // Cleanup on unmount
        return () => {
            ws.current?.close();
        };
    }, [setPhasePicking, setWaveForms, stationCode]);

    return (
        <>{children}</>
    )
}