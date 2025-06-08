'use server'

import {Station} from "@/modules/station/components/StationList/interface";
import CustomCheckbox from "@/modules/common/components/Checkbox";

export default async function StationList({
    stations
}: {stations: Station[]}) {
    return (
        <div className={'flex flex-col gap-2 w-full'}>
            <span className={'text-lg font-bold'}>Available Stations</span>
            <div className={'flex flex-col gap-2 max-h-80 overflow-y-scroll'}>
                {stations.map((station) => (
                    <div key={station.code} className={'rounded-lg bg-gray-600/50 p-2 flex justify-between items-center'}>
                        <span className={'font-semibold'}>{station.code}</span>
                        <CustomCheckbox checked={station.is_enabled}/>
                    </div>
                ))}
            </div>
        </div>
    )
}