import {create} from "zustand/react";
import {UseWaveFormStoreInterface} from "@/modules/waveForm/stores/interface";

export const useWaveFormStore = create<UseWaveFormStoreInterface>((set) => ({
    waveForms: {
        BHZ: [],
        BHN: [],
        BHE: []
    },
    selectedStation: null,
    setWaveForms: (waveForm, station) => {
        set((state) => {
            let combined;

            if (station === state.selectedStation) {
                const existing = state.waveForms[waveForm.channel] || [];
                combined = [...existing, ...waveForm.data];
            } else {
                combined = waveForm.data;
            }

            combined.sort((a, b) => a.time - b.time);

            const combinedLength = combined.length;

            const grouped = new Map();

            for (const { time, value } of combined) {
                if (!grouped.has(time)) {
                    grouped.set(time, { sum: value, count: 1 });
                } else {
                    const g = grouped.get(time);
                    g.sum += value;
                    g.count += 1;
                    grouped.set(time, g);
                }
            }

            const aggregated = Array.from(grouped.entries()).map(([time, { sum, count }]) => ({
                time,
                value: sum / count,
            }));

            const trimmed = aggregated.length === combinedLength ? aggregated.slice(aggregated.length * 0.1) : aggregated;

            return {
                waveForms: {
                    ...state.waveForms,
                    [waveForm.channel]: trimmed,
                },
                selectedStation: station,
            };
        });
    },
}));