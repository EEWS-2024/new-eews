'use server'

import { makeRequest } from '@/modules/common/actions/makeRequest'
import {ToggleStationRequestInterface} from "@/modules/station/actions/toggleStation/interface";

export const toggleStations = async (body: ToggleStationRequestInterface) => {
     await makeRequest<null>({
        path: `station`,
        method: 'POST',
        body: body
    })

    return body.code
}
