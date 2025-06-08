import {create} from "zustand/react";
import {UseStationStoreInterface} from "@/modules/station/stores/interface";

export const useStationStore = create<UseStationStoreInterface>((set) => ({
    station: null,
    setStation: (station) => set({station}),
}));
