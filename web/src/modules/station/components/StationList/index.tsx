'use client'

import {Station} from "@/modules/station/components/StationList/interface";
import CustomCheckbox from "@/modules/common/components/Checkbox";
import {useMutation, useQueryClient} from "@tanstack/react-query";
import {toggleStations} from "@/modules/station/actions/toggleStation";
import {Skeleton} from "@/modules/common/components/Skeleton";

export default function StationList({
    stations,
    isLoading,
}: {stations?: Station[], isLoading?: boolean}) {
    const queryClient = useQueryClient()

    const {mutate} = useMutation({
        mutationFn: async ({stationCode, isEnabled}: {
            stationCode: string,
            isEnabled: boolean
        }) => await toggleStations({
            code: stationCode,
            is_enabled: isEnabled
        }),
        onSuccess: async () => await queryClient.invalidateQueries({ queryKey: ['stations'] }),
    })

    return (
        <div className={'flex flex-col gap-2 w-full'}>
            <span className={'text-lg font-bold'}>Available Stations</span>
            <div className={'flex flex-col gap-2 max-h-80 overflow-y-scroll'}>
                {
                    isLoading
                        ? (
                            <>
                                <Skeleton width="100%" height={40} />
                                <Skeleton width="100%" height={40} />
                                <Skeleton width="100%" height={40} />
                                <Skeleton width="100%" height={40} />
                                <Skeleton width="100%" height={40} />
                                <Skeleton width="100%" height={40} />
                                <Skeleton width="100%" height={40} />
                            </>
                        ) :
                        !isLoading && !stations
                            ? <div className={'w-full flex justify-center items-center'}>Something went wrong</div>
                            : !!stations && stations.length <= 0
                            ? <div className={'w-full flex justify-center items-center'}>No Stations</div>
                            : stations?.map((station) => (
                                    <div key={station.code} className={'rounded-lg bg-gray-600/50 p-2 flex justify-between items-center'}>
                                        <span className={'font-semibold'}>{station.code}</span>
                                        <CustomCheckbox checked={station.is_enabled} onChange={() => mutate({
                                            stationCode: station.code,
                                            isEnabled: !station.is_enabled
                                        })}/>
                                    </div>
                                ))
                }
            </div>
            <div className={'w-full justify-center'}>
                <button className={'bg-indigo-600 text-white w-full rounded-xl py-1 font-bold'}>Stream</button>
            </div>
        </div>
    )
}