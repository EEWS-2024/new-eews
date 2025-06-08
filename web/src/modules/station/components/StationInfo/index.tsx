'use client';

import {useStationStore} from "@/modules/station/stores";

export default function StationInfo() {
    const {station} = useStationStore()
    return (
        <div className={'w-full flex items-center gap-2 px-2'}>
            {
                station
                    ? <span className={'text-white font-bold text-xl'}>{station?.code}</span>
                    : <span className={'text-white font-bold text-xl'}>No Station Selected</span>
            }
        </div>
    )
}