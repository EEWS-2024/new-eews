import {Station} from "@/modules/station/components/StationList/interface";

export interface UseStationStoreInterface {
    station: Station | null;
    setStation: (station: Station | null) => void;
}