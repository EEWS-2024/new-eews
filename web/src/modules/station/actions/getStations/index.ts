'use server'

import { makeRequest } from '@/modules/common/actions/makeRequest'
import {GetStationResponseInterface} from "@/modules/station/actions/getStations/interface";

export const getStations = async () => {
    return await makeRequest<
        GetStationResponseInterface[]
    >({
        path: `station/`,
        method: 'GET',
    })
}
