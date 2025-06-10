
export interface GetStationResponseInterface {
  code: string
  name: string
  latitude: number
  longitude: number
  elevation: number
  nearest_stations: string[],
  is_enabled: boolean
}

