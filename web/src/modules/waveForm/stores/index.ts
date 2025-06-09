import {create} from "zustand/react";
import {UseWaveFormStoreInterface} from "@/modules/waveForm/stores/interface";

export const useWaveFormStore = create<UseWaveFormStoreInterface>((set) => ({
    waveForms: {},
    selectedStation: null,
    setWaveForms: (waveForm) => {
        set((state) => {
            const newPayload = {
                start_time: waveForm.start_time,
                end_time: waveForm.end_time,
                sampling_rate: waveForm.sampling_rate,
                arrival_time: waveForm.arrival_time,
                data: waveForm.data,
            }

            if (waveForm.station === state.selectedStation) {
                const existingWaveForms = state.waveForms[waveForm.channel] || [];
                const newWaveForms = [...existingWaveForms, newPayload];
                return {
                    waveForms: {
                        ...state.waveForms,
                        [waveForm.channel]: newWaveForms,
                    },
                };
            }

            return {
                waveForms: {
                    [waveForm.channel]: [newPayload],
                },
                selectedStation: waveForm.station,
            };
        });
    },
}));