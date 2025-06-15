'use client'

import {Station} from "@/modules/station/components/StationList/interface";
import CustomCheckbox from "@/modules/common/components/Checkbox";
import {useMutation, useQueryClient} from "@tanstack/react-query";
import {toggleStations} from "@/modules/station/actions/toggleStation";
import {Skeleton} from "@/modules/common/components/Skeleton";
import StreamButton from "@/modules/waveForm/components/StreamButton";
import {useParams, useRouter, useSearchParams} from "next/navigation";
import {useStationStore} from "@/modules/station/stores";
import {Input} from "@/modules/common/components/Input";
import React, {useState} from "react";

export default function StationList({
    stations,
    isLoading,
}: {stations?: Station[], isLoading?: boolean}) {
    const searchParams = useSearchParams()
    const stationCode = searchParams.get("stationCode")
    const router = useRouter()
    const {streamType} = useParams()
    const queryClient = useQueryClient()
    const {setStation} = useStationStore()

    const [modelType, setModelType] = useState<string>('')
    const [retrievalTime, setRetrievalTime] = useState({
        startTime: null,
        endTime: null,
    })

    const handleDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setRetrievalTime((prev) => ({
           ...prev,
           [e.target.name]: e.target.value,
        }))
    }

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
                router.replace(`/${streamType}`)
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
                <select className={'w-full p-2 bg-gray-600/50 rounded-xl'} value={modelType} onChange={(e) => setModelType(e.target.value)}>
                    <option className={'text-black'} value={''}>Select Model</option>
                    <option className={'text-black'} value={'unet-custom'}>U-net Custom</option>
                    <option className={'text-black'} value={'phasenet'}>Phasenet</option>
                </select>
                {
                    streamType === 'archive' && (
                        <div className={'w-full flex gap-2 flex-col'}>
                            <div className={'flex items-center gap-2'}>
                                <label htmlFor={'start-time'} className={'w-1/6'}>Start: </label>
                                <Input id={'start-time'} className={'w-5/6'} type={'datetime-local'} name={'startTime'} onChange={handleDateChange}/>
                            </div>
                            <div className={'flex items-center gap-2'}>
                                <label htmlFor={'end-time'} className={'w-1/6'}>Finish: </label>
                                <Input id={'end-time'} className={'w-5/6'} type={'datetime-local'} name={'endTime'} onChange={handleDateChange}/>
                            </div>
                        </div>
                    )
                }
                <StreamButton {...retrievalTime} modelType={modelType}/>
            </div>
        </div>
    )
}