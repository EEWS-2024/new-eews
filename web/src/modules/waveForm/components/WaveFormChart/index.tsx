'use client';

import {useWaveFormStore} from "@/modules/waveForm/stores";
import {useSearchParams} from "next/navigation";
import Chart from "@/modules/common/components/Chart";

export default function WaveFormChart() {
    const {waveForms} = useWaveFormStore()
    const searchParams = useSearchParams()
    const stationCode = searchParams.get('stationCode');

    return (
        <div className={`w-full h-full flex ${!stationCode ? 'items-center justify-center bg-gray-600/50 p-4 rounded-2xl' : 'gap-4'}`}>
            {!stationCode
                ? <span className={'text-white font-bold text-xl'}>No Station Selected</span> :
                Object.entries(waveForms).map(([key, value]) => (
                <div key={key} className={'w-full h-full flex flex-col gap-2 bg-gray-600/50 p-4 rounded-2xl'}>
                    <span className={'text-white font-bold text-xl'}>{key}</span>
                    {value.length <= 0
                        ? <span className={'w-full h-full justify-center items-center flex animate-pulse'}>Retrieving Data...</span>
                        : <Chart data={value}/>
                    }
                </div>
            ))}
        </div>
    )
}