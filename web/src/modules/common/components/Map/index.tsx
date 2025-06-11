'use client'

import {Station} from "@/modules/station/components/StationList/interface";
import {MapContainer, Marker, Popup, TileLayer} from "react-leaflet";
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import {useRouter} from "next/navigation";
import {useWaveFormStore} from "@/modules/waveForm/stores";

delete (L.Icon.Default.prototype as any)._getIconUrl;

L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
    iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
    shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

export default function Map({stations}: {stations?: Station[]}) {
    const {epic} = useWaveFormStore()
    const router = useRouter()

    const earthquakeMarker = L.divIcon({
        html: '<div class="w-5 h-5 bg-red-600 rounded-full border-2 border-white shadow-md animate-ping"></div>',
        className: '', // Prevent Leaflet's default styling
        iconSize: [20, 20],
        iconAnchor: [10, 10],
    });

    return (
        <div className={'w-full h-full rounded-2xl overflow-hidden'}>
            <MapContainer id={'map'} center={[-2, 118]} zoom={4} scrollWheelZoom className="w-full h-full">
                <TileLayer
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    attribution="&copy; OpenStreetMap contributors"
                />
                {stations?.map((station) => (
                    <Marker
                        eventHandlers={{
                            click: async () =>  router.push(`?stationCode=${station.code}`)
                        }}
                        key={station.code}
                        position={[station.latitude, station.longitude]}
                    >
                        <Popup>
                            <div className={'flex flex-col gap-2'}>
                                <span className={'font-bold'}>{station.name.replaceAll('GEFON Station', '')}</span>
                                <span>Code: {station.code}</span>
                                <span>Longitude: {station.longitude}</span>
                                <span>Latitude: {station.latitude}</span>
                                <span>Elevation: {station.elevation}</span>
                            </div>
                        </Popup>
                    </Marker>
                ))}
                {
                    epic && (
                        <Marker position={[epic.latitude, epic.longitude]} icon={earthquakeMarker} >
                            <Popup>
                                <div className={'flex flex-col gap-2'}>
                                    <span>Nearest Stations: {epic.station_codes.join(", ")}</span>
                                    <span>Magnitude: {epic.magnitude.toFixed(2)}</span>
                                    <span>Longitude: {epic.longitude.toFixed(2)}</span>
                                    <span>Latitude: {epic.latitude.toFixed(2)}</span>
                                </div>
                            </Popup>
                        </Marker>
                    )
                }
            </MapContainer>
        </div>
    );
}
