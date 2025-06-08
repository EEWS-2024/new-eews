'use client'

import {Station} from "@/modules/station/components/StationList/interface";
import {MapContainer, Marker, Popup, TileLayer} from "react-leaflet";
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

delete (L.Icon.Default.prototype as any)._getIconUrl;

L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
    iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
    shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

export default function Map({stations}: {stations: Station[]}) {
    return (
        <div className={'w-full h-full rounded-2xl overflow-hidden'}>
            {/*<Map*/}
            {/*    mapboxAccessToken={process.env.NEXT_PUBLIC_MAPBOX_API_KEY}*/}
            {/*    initialViewState={{*/}
            {/*        longitude: 118,*/}
            {/*        latitude: -2,*/}
            {/*        zoom: 4,*/}
            {/*    }}*/}
            {/*    mapStyle="mapbox://styles/mapbox/streets-v9"*/}
            {/*>*/}
            {/*    {stations.map((station) => (*/}
            {/*        <Marker key={station.code} longitude={station.longitude} latitude={station.latitude} />*/}
            {/*    ))}*/}
            {/*</Map>*/}
            <MapContainer center={[-2, 118]} zoom={4} scrollWheelZoom className="w-full h-full">
                <TileLayer
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    attribution="&copy; OpenStreetMap contributors"
                />
                {stations.map((station) => (
                    <Marker key={station.code} position={[station.latitude, station.longitude]}>
                        <Popup>
                            A pretty CSS3 popup. <br /> Easily customizable.
                        </Popup>
                    </Marker>
                ))}
            </MapContainer>
        </div>
    );
}
