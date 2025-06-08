'use server';

import MapContainer from "../../modules/common/components/Map";
import {getStations} from "@/modules/station/actions/getStations";
import StationList from "@/modules/station/components/StationList";

export default async function LivePage() {
    const stations = await getStations()

    return (
        <div className={'w-full h-screen'}>
            <div className={'w-full flex flex-col gap-4'}>
                <div className={'w-full grid grid-cols-12 gap-4 row-span-5 h-full'}>
                    <div className={'col-span-9 h-full bg-gray-600/50 rounded-2xl p-2'}>
                        <MapContainer stations={stations}/>
                    </div>
                    <div className={'col-span-3 grid grid-rows-6 h-full gap-3'}>
                        <div className={'rounded-2xl bg-gray-600/50 flex justify-center items-center row-span-1'}>
                            <span>No Station Selected</span>
                        </div>
                        <div className={'' +
                            'rounded-2xl bg-gray-600/50 flex row-span-5 p-2'
                        }>
                            <StationList stations={stations}/>
                        </div>
                    </div>
                </div>
                <div className={'w-full row-span-1 bg-gray-600/50 flex justify-center items-center rounded-2xl'}>
                    <span>Channel 1</span>
                </div>
                <div className={'w-full row-span-1 bg-gray-600/50 flex justify-center items-center rounded-2xl'}>
                    <span>Channel 1</span>
                </div>
                <div className={'w-full row-span-1 bg-gray-600/50 flex justify-center items-center rounded-2xl'}>
                    <span>Channel 1</span>
                </div>
            </div>
        </div>
    )
}