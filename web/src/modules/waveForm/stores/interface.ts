
export interface WaveFormResponseInterface {
    channel: string
    data: {
        time: number
        value: number
    }[]
}

export interface PhasePickingResponseInterface {
    channel: string
    is_p_arrived: boolean
    p_arrival_time: number
    is_s_arrived: boolean
    s_arrival_time: number
}

export interface EpicWaveFormResponseInterface {
    station_codes: string[]
    magnitude: number
    latitude: number
    longitude: number
}

export interface UseWaveFormStoreInterface {
    waveForms: {
        [channelCode: string]: {
            time: number
            value: number
        }[]
    };
    selectedStation: string | null;
    phasePicking: {
        [channelCode: string]: {
            pArrivalTime: number | null,
            sArrivalTime: number | null
        }
    }
    epic: EpicWaveFormResponseInterface | null
    isStreaming: boolean
    setWaveForms: (waveForm: WaveFormResponseInterface, station: string) => void;
    resetWaveForms: () => void;
    setPhasePicking: (phasePicking: PhasePickingResponseInterface) => void;
    resetPhasePicking: () => void;
    setEpic: (epic: EpicWaveFormResponseInterface) => void;
    resetEpic: () => void;
    setIsStreaming: (isStreaming: boolean) => void;
}