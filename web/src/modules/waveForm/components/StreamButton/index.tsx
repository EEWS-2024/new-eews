'use client'

import {useMutation, useQuery, useQueryClient} from "@tanstack/react-query";
import {getStreamStatus} from "@/modules/waveForm/actions/getStreamStatus";
import {useEffect} from "react";
import {useWaveFormStore} from "@/modules/waveForm/stores";
import {useParams} from "next/navigation";
import {startStream} from "@/modules/waveForm/actions/startStream";
import {stopStream} from "@/modules/waveForm/actions/stopStream";
import toast from "react-hot-toast";

export default function StreamButton({startTime, endTime}: {
    startTime: Date | null;
    endTime: Date | null;
}) {
    const {streamType: paramStreamType} = useParams()
    const streamType = paramStreamType?.toString().toUpperCase()

    const {setIsStreaming, isStreaming} = useWaveFormStore()
    const {data: streamStatus, isLoading} = useQuery({
        queryKey: ['stream'],
        queryFn: () => getStreamStatus()
    })

    const queryClient = useQueryClient()

    const {mutate: startStreaming, isPending: startStreamingPending} = useMutation({
        mutationFn: ({streamType, startTime, endTime}: {streamType: string, startTime: Date | null, endTime: Date | null}) => startStream({
            stream_type: streamType,
            start_time: startTime || null,
            end_time: endTime || null,
        }),
        onSuccess: async () => await queryClient.invalidateQueries({queryKey: ['stream']}),
        onError: error => toast.error(error.message),
    })

    const {mutate: stopStreaming, isPending: stopStreamingPending} = useMutation({
        mutationFn: ({streamType}: {streamType: string}) => stopStream({
            stream_type: streamType,
        }),
        onSuccess: async () => await queryClient.invalidateQueries({queryKey: ['stream']})
    })

    useEffect(() => {
        if (streamStatus && streamType) {
            setIsStreaming(streamStatus[streamType])
        }
    }, [streamStatus, streamType, setIsStreaming])

    return (
        <div className={'w-full justify-center'}>
            <button
                onClick={() => !isStreaming ? startStreaming({streamType: streamType!, startTime, endTime}) : stopStreaming({streamType: streamType!})}
                className={'bg-indigo-600 text-white w-full rounded-xl py-1 font-bold hover:bg-indigo-800 cursor-pointer'}>
                {isLoading || startStreamingPending || stopStreamingPending
                    ? <span className={'animate-pulse'}>Loading...</span>
                    : isStreaming
                        ? 'Stop'
                        : 'Stream'}
            </button>
        </div>
    )
}