'use server'

import { makeRequest } from '@/modules/common/actions/makeRequest'
import {StopStreamRequestInterface} from "@/modules/waveForm/actions/stopStream/interface";

export const stopStream = async (body: StopStreamRequestInterface) => {
    return await makeRequest<
        string
    >({
        path: `stream/stop`,
        method: 'POST',
        body
    })
}
