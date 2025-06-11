'use server'

import { makeRequest } from '@/modules/common/actions/makeRequest'
import {GetStreamStatusResponseInterface} from "@/modules/waveForm/actions/getStreamStatus/interface";

export const getStreamStatus = async () => {
    return await makeRequest<
        GetStreamStatusResponseInterface
    >({
        path: `stream/status`,
        method: 'GET',
    })
}
