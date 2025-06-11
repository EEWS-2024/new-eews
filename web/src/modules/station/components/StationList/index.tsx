'use client'

import {Station} from "@/modules/station/components/StationList/interface";
import CustomCheckbox from "@/modules/common/components/Checkbox";
import {useMutation, useQueryClient} from "@tanstack/react-query";
import {toggleStations} from "@/modules/station/actions/toggleStation";
import {Skeleton} from "@/modules/common/components/Skeleton";
import StreamButton from "@/modules/waveForm/components/StreamButton";
import {usePathname, useRouter, useSearchParams} from "next/navigation";
import {useStationStore} from "@/modules/station/stores";

export default function StationList({
    stations,
    isLoading,
}: {stations?: Station[], isLoading?: boolean}) {
    const searchParams = useSearchParams()
    const stationCode = searchParams.get("stationCode")
    const router = useRouter()
    const pathname = usePathname()
    const queryClient = useQueryClient()
    const {setStation} = useStationStore()

    const {mutate} = useMutation({
        mutationFn: async ({stationCode, isEnabled}: {
            stationCode: string,
            isEnabled: boolean
        }) => await toggleStations({
            code: stationCode,
            is_enabled: isEnabled
        }),
        onSuccess: async (toggledStationCode) => {
            if (stationCode === toggledStationCode) {
                router.replace(pathname)
                setStation(null)
            }
            await queryClient.invalidateQueries({ queryKey: ['stations'] })
        },
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
            <div className={'flex flex-col gap-2'}>
                <select className={'w-full p-2 bg-gray-600/50 rounded-xl'}>
                    <option className={'text-black'}>Select Model</option>
                    <option className={'text-black'}>Custom</option>
                    <option className={'text-black'}>Phasenet</option>
                </select>
                <StreamButton/>
            </div>
        </div>
    )
}