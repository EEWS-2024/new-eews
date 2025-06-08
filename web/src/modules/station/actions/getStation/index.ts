'use server'

import { makeRequest } from '@/modules/common/actions/makeRequest'
import {GetStationResponseInterface} from "@/modules/station/actions/getStations/interface";

export const getStation = async (code: string) => {
    return await makeRequest<
        GetStationResponseInterface | null
    >({
        path: `station/${code}`,
        method: 'GET',
    })
}
