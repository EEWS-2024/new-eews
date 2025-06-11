'use server'

import { makeRequest } from '@/modules/common/actions/makeRequest'
import {StartStreamRequestInterface} from "@/modules/waveForm/actions/startStream/interface";

export const startStream = async (body: StartStreamRequestInterface) => {
    return await makeRequest<
        string
    >({
        path: `stream/start`,
        method: 'POST',
        body
    })
}
