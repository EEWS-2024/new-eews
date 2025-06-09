'use client';

import {useWaveFormStore} from "@/modules/waveForm/stores";
import {useSearchParams} from "next/navigation";
import Chart from "@/modules/common/components/Chart";
import {generateTimeSeries} from "@/modules/waveForm/utils/generate-timeseries";

export default function WaveFormChart() {
    const {waveForms} = useWaveFormStore()
    const searchParams = useSearchParams()
    const stationCode = searchParams.get('stationCode');

    if (!stationCode) {
        return (
            <div className={'w-full h-full flex items-center justify-center'}>
                <span className={'text-white font-bold text-xl'}>No Station Selected</span>
            </div>
        )
    }

    return (
        <div className={'w-full flex flex-col gap-4 p-4'}>
            {Object.entries(waveForms).map(([key, value]) => (
                <div key={key} className={'w-full h-full flex flex-col gap-2'}>
                    <span className={'text-white font-bold text-xl'}>{key}</span>
                    <Chart data={generateTimeSeries(value, 20.0)} interval={Math.floor(value.length / 9) - 10}/>
                </div>
            ))}
        </div>
    )
}