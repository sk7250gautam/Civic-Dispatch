import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import { MapPin, Navigation } from 'lucide-react';
import { StatusBadge } from './StatusBadge';
import { PriorityBadge } from './PriorityBadge';

// Fix Leaflet's missing default marker icon in bundlers
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

interface GrievanceMapProps {
  mode?: 'picker' | 'viewer';
  initialLat?: number;
  initialLng?: number;
  zoom?: number;
  markers?: Array<{
    id: number | string;
    lat: number;
    lng: number;
    title?: string;
    reference_id?: string;
    category?: string;
    status?: string;
    priority?: string;
  }>;
  onLocationSelect?: (lat: number, lng: number) => void;
  height?: string;
}

// Subcomponent to handle map clicks in picker mode
const LocationPickerHandler: React.FC<{ onPick: (lat: number, lng: number) => void }> = ({ onPick }) => {
  useMapEvents({
    click(e) {
      onPick(e.latlng.lat, e.latlng.lng);
    },
  });
  return null;
};

export const GrievanceMap: React.FC<GrievanceMapProps> = ({
  mode = 'viewer',
  initialLat = 12.9716,
  initialLng = 77.5946,
  zoom = 13,
  markers = [],
  onLocationSelect,
  height = '400px',
}) => {
  const [selectedLocation, setSelectedLocation] = useState<[number, number]>([initialLat, initialLng]);

  useEffect(() => {
    setSelectedLocation([initialLat, initialLng]);
  }, [initialLat, initialLng]);

  const handlePick = (lat: number, lng: number) => {
    const roundedLat = parseFloat(lat.toFixed(6));
    const roundedLng = parseFloat(lng.toFixed(6));
    setSelectedLocation([roundedLat, roundedLng]);
    if (onLocationSelect) {
      onLocationSelect(roundedLat, roundedLng);
    }
  };

  const handleUseMyLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        pos => {
          handlePick(pos.coords.latitude, pos.coords.longitude);
        },
        () => {
          alert('Could not retrieve device GPS location. Please click on the map manually.');
        }
      );
    }
  };

  return (
    <div className="relative rounded-lg overflow-hidden border border-slate-200 shadow-sm" style={{ height }}>
      {mode === 'picker' && (
        <div className="absolute top-3 right-3 z-[1000] flex gap-2">
          <button
            type="button"
            onClick={handleUseMyLocation}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-white text-slate-800 text-xs font-semibold rounded-md shadow-md border border-slate-200 hover:bg-slate-50 transition"
          >
            <Navigation className="w-3.5 h-3.5 text-civic-teal-600" />
            Use My GPS Location
          </button>
        </div>
      )}

      <MapContainer
        center={[initialLat, initialLng]}
        zoom={zoom}
        style={{ height: '100%', width: '100%' }}
        scrollWheelZoom={false}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {mode === 'picker' ? (
          <>
            <LocationPickerHandler onPick={handlePick} />
            <Marker position={selectedLocation}>
              <Popup>
                <div className="text-xs">
                  <div className="font-semibold text-slate-900">Selected Grievance Location</div>
                  <div className="text-slate-600 font-mono mt-0.5">
                    {selectedLocation[0]}, {selectedLocation[1]}
                  </div>
                  <div className="text-[10px] text-slate-400 mt-1">Click anywhere on the map to relocate pin.</div>
                </div>
              </Popup>
            </Marker>
          </>
        ) : (
          markers.map(m => (
            <Marker key={m.id} position={[m.lat, m.lng]}>
              <Popup>
                <div className="text-xs p-1 max-w-[220px]">
                  {m.reference_id && (
                    <div className="font-mono font-bold text-navy-900 mb-1">{m.reference_id}</div>
                  )}
                  {m.title && <div className="font-medium text-slate-800 mb-2">{m.title}</div>}
                  <div className="flex flex-wrap gap-1 mb-2">
                    {m.status && <StatusBadge status={m.status} size="sm" />}
                    {m.priority && <PriorityBadge priority={m.priority} showIcon={false} />}
                  </div>
                  <div className="text-[10px] text-slate-500 font-mono">
                    Coord: {m.lat}, {m.lng}
                  </div>
                </div>
              </Popup>
            </Marker>
          ))
        )}
      </MapContainer>
    </div>
  );
};
