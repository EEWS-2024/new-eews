'use client'

import {Station} from "@/modules/station/components/StationList/interface";
import {MapContainer, Marker, Popup, TileLayer} from "react-leaflet";
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import {getStation} from "@/modules/station/actions/getStation";
import {useStationStore} from "@/modules/station/stores";
import {useRouter} from "next/navigation";

delete (L.Icon.Default.prototype as any)._getIconUrl;

L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
    iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
    shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

export default function Map({stations}: {stations: Station[]}) {
    const {setStation} = useStationStore()
    const router = useRouter()
    return (
        <div className={'w-full h-full rounded-2xl overflow-hidden'}>
            <MapContainer center={[-2, 118]} zoom={4} scrollWheelZoom className="w-full h-full">
                <TileLayer
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    attribution="&copy; OpenStreetMap contributors"
                />
                {stations.map((station) => (
                    <Marker
                        eventHandlers={{
                            click: async () => {
                                const result = await getStation(station.code)
                                if (result) {
                                    router.push(`?stationCode=${result.code}`);
                                }
                                setStation(result)
                            }
                        }}
                        key={station.code}
                        position={[station.latitude, station.longitude]}
                    >
                        <Popup>
                            <div className={'flex flex-col gap-2'}>
                                <span>Code: {station.code}</span>
                                <span>Longitude: {station.longitude}</span>
                                <span>Latitude: {station.latitude}</span>
                                <span>Elevation: {station.elevation}</span>
                            </div>
                        </Popup>
                    </Marker>
                ))}
            </MapContainer>
        </div>
    );
}
