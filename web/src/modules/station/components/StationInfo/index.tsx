'use client';

import {useStationStore} from "@/modules/station/stores";

export default function StationInfo() {
    const {station} = useStationStore()
    return (
        <div className={`w-full flex items-center gap-2 p-2 ${!station ? 'justify-center': ''}`}>
            {
                station
                    ? <>
                        <span className={'text-white font-bold'}>{station?.name.replaceAll("GEOFON Station", "")}</span>
                        <span className={'text-white/50 '}>({station?.code})</span>
                    </>
                    : <span className={'text-white font-bold text-xl'}>No Station Selected</span>
            }
        </div>
    )
}