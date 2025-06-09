
export interface WaveFormResponseInterface {
    network: string
    station: string
    channel: string
    location: string
    start_time: string
    end_time: string
    delta: number
    npts: number
    calib: number
    sampling_rate: number
    arrival_time: number
    type: string
    data: number[]
}

export interface WaveForm {
    start_time: string
    end_time:string
    sampling_rate: number
    arrival_time: number
    data: number[]
}

export interface UseWaveFormStoreInterface {
    waveForms: {
        [channelCode: string]: WaveForm[]
    };
    selectedStation: string | null;
    setWaveForms: (waveForm: WaveFormResponseInterface) => void;
}