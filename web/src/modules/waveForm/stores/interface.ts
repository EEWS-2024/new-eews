
export interface WaveFormResponseInterface {
    channel: string
    data: {
        time: number
        value: number
    }[]
}

export interface UseWaveFormStoreInterface {
    waveForms: {
        [channelCode: string]: {
            time: number
            value: number
        }[]
    };
    selectedStation: string | null;
    setWaveForms: (waveForm: WaveFormResponseInterface, station: string) => void;
}