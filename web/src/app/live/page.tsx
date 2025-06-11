'use client';

import MapContainer from "../../modules/common/components/Map";
import {getStations} from "@/modules/station/actions/getStations";
import StationList from "@/modules/station/components/StationList";
import StationInfo from "@/modules/station/components/StationInfo";
import WaveFormChart from "@/modules/waveForm/components/WaveFormChart";
import {useQuery} from "@tanstack/react-query";

export default function LivePage() {
    const {data: stations, isLoading} = useQuery({
        queryKey: ['stations'],
        queryFn: () => getStations(),
    })

    return (
        <div className={'w-full h-screen'}>
            <div className={'w-full flex flex-col gap-4 h-full'}>
                <div className={'w-full grid grid-cols-12 gap-4 row-span-5 h-full'}>
                    <div className={'col-span-9 h-full bg-gray-600/50 rounded-2xl p-2'}>
                        <MapContainer stations={stations}/>
                    </div>
                    <div className={'col-span-3 flex flex-col h-full gap-3'}>
                        <div className={'rounded-2xl bg-gray-600/50 flex justify-center items-center'}>
                            <StationInfo />
                        </div>
                        <div className={
                            'rounded-2xl bg-gray-600/50 flex p-2'
                        }>
                            <StationList stations={stations} isLoading={isLoading}/>
                        </div>
                    </div>
                </div>
                <WaveFormChart/>
            </div>
        </div>
    )
}