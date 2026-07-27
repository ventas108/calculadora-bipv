import { useEffect, useRef, useState } from 'react';
import { MapPin, Search, Plus, Trash2, AlertCircle, Loader } from 'lucide-react';
import { MapView } from './Map';
import { toast } from 'sonner';

interface CityMarker {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  country: string;
  hasEPW: boolean;
}

interface CityMapExplorerProps {
  cities: CityMarker[];
  onSelectCity?: (city: CityMarker) => void;
  onAddCity?: (latitude: number, longitude: number) => void;
  onDeleteCity?: (id: string) => void;
}

export default function CityMapExplorer({ cities, onSelectCity, onAddCity, onDeleteCity }: CityMapExplorerProps) {
  const mapRef = useRef<google.maps.Map | null>(null);
  const markersRef = useRef<google.maps.marker.AdvancedMarkerElement[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedMarker, setSelectedMarker] = useState<CityMarker | null>(null);
  const [latitude, setLatitude] = useState('');
  const [longitude, setLongitude] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [searching, setSearching] = useState(false);

  // Manejar cuando el mapa está listo
  const handleMapReady = (map: google.maps.Map) => {
    mapRef.current = map;
    setError(null);

    // Click en el mapa para capturar coordenadas
    map.addListener('click', (event: google.maps.MapMouseEvent) => {
      if (event.latLng) {
        const lat = event.latLng.lat();
        const lng = event.latLng.lng();
        setLatitude(lat.toFixed(4));
        setLongitude(lng.toFixed(4));
        toast.success('Coordenadas capturadas del mapa');
      }
    });

    // Actualizar marcadores iniciales
    updateMarkers(map);
  };

  // Actualizar marcadores en el mapa
  const updateMarkers = (map: google.maps.Map) => {
    // Limpiar marcadores anteriores
    markersRef.current.forEach(marker => marker.remove());
    markersRef.current = [];

    // Crear nuevos marcadores
    cities.forEach(city => {
      const marker = new google.maps.marker.AdvancedMarkerElement({
        map: map,
        position: { lat: city.latitude, lng: city.longitude },
        title: city.name,
      });

      // Crear contenido del InfoWindow
      const infoContent = document.createElement('div');
      infoContent.style.fontSize = '12px';
      infoContent.style.fontFamily = 'Arial';
      infoContent.style.padding = '8px';
      infoContent.innerHTML = `
        <strong>${city.name}</strong><br/>
        ${city.country}<br/>
        Lat: ${city.latitude.toFixed(4)}°<br/>
        Lng: ${city.longitude.toFixed(4)}°<br/>
        ${city.hasEPW ? '✓ Con datos EPW' : '✗ Sin datos EPW'}
      `;

      const infoWindow = new google.maps.InfoWindow({
        content: infoContent,
      });

      marker.addListener('click', () => {
        infoWindow.open({
          anchor: marker,
          map: map,
        });
        setSelectedMarker(city);
        if (onSelectCity) onSelectCity(city);
      });

      markersRef.current.push(marker);
    });
  };

  // Actualizar marcadores cuando cambian las ciudades
  useEffect(() => {
    if (mapRef.current) {
      updateMarkers(mapRef.current);
    }
  }, [cities]);

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      toast.error('Por favor ingresa una ubicación');
      return;
    }

    if (!mapRef.current) {
      toast.error('El mapa no está listo. Intenta de nuevo.');
      return;
    }

    setSearching(true);

    try {
      // Verificar que Google Maps esté disponible
      if (!window.google || !window.google.maps) {
        toast.error('Google Maps no está disponible');
        setSearching(false);
        return;
      }

      const geocoder = new window.google.maps.Geocoder();

      geocoder.geocode(
        { address: searchQuery },
        (results, status) => {
          setSearching(false);

          if (status === window.google.maps.GeocoderStatus.OK && results && results.length > 0) {
            const location = results[0].geometry.location;
            const lat = location.lat();
            const lng = location.lng();

            // Actualizar el mapa
            if (mapRef.current) {
              mapRef.current.setCenter({ lat, lng });
              mapRef.current.setZoom(12);
            }

            // Actualizar los campos de coordenadas
            setLatitude(lat.toFixed(4));
            setLongitude(lng.toFixed(4));

            const address = results[0].formatted_address;
            toast.success(`✓ Ubicación encontrada: ${address}`);
            
            console.log('Geocoding exitoso:', { lat, lng, address });
          } else if (status === window.google.maps.GeocoderStatus.ZERO_RESULTS) {
            toast.error(`No se encontraron resultados para "${searchQuery}"`);
            console.warn('Geocoding ZERO_RESULTS:', searchQuery);
          } else {
            toast.error(`Error: ${status}`);
            console.error('Geocoding error:', status);
          }
        }
      );
    } catch (err) {
      setSearching(false);
      toast.error('Error al procesar la búsqueda');
      console.error('Geocoding exception:', err);
    }
  };

  const handleAddCity = () => {
    if (!latitude || !longitude) {
      toast.error('Por favor ingresa coordenadas válidas');
      return;
    }

    const lat = parseFloat(latitude);
    const lng = parseFloat(longitude);

    if (isNaN(lat) || isNaN(lng)) {
      toast.error('Las coordenadas deben ser números válidos');
      return;
    }

    if (lat < -90 || lat > 90 || lng < -180 || lng > 180) {
      toast.error('Coordenadas fuera de rango');
      return;
    }

    if (onAddCity) {
      onAddCity(lat, lng);
      setLatitude('');
      setLongitude('');
      toast.success('Ubicación agregada');
    }
  };

  const handleZoomToCity = (city: CityMarker) => {
    if (!mapRef.current) return;
    mapRef.current.setCenter({ lat: city.latitude, lng: city.longitude });
    mapRef.current.setZoom(12);
    setSelectedMarker(city);
  };

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <div className="flex items-center gap-3 mb-4">
          <AlertCircle className="text-red-600" size={20} />
          <h3 className="font-semibold text-red-900">Error al cargar Google Maps</h3>
        </div>
        <p className="text-red-800 mb-4">{error}</p>
        <p className="text-sm text-red-700">Puedes usar la pestaña "Ciudades" para gestionar tus ubicaciones sin el mapa.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-gradient-to-r from-blue-50 to-cyan-50 border border-blue-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <MapPin size={20} className="text-blue-600" />
          Explorador de Ciudades en Mapa
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          {/* Búsqueda */}
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="Ej: Bogotá, Colombia o Calle 5 #10-20"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              disabled={searching}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
            />
            <button
              onClick={handleSearch}
              disabled={searching}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2 disabled:bg-gray-400"
            >
              {searching ? (
                <>
                  <Loader size={16} className="animate-spin" />
                  Buscando...
                </>
              ) : (
                <>
                  <Search size={16} />
                  Buscar
                </>
              )}
            </button>
          </div>

          {/* Latitud */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Latitud</label>
            <input
              type="text"
              placeholder="-90 a 90"
              value={latitude}
              onChange={(e) => setLatitude(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Longitud */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Longitud</label>
            <input
              type="text"
              placeholder="-180 a 180"
              value={longitude}
              onChange={(e) => setLongitude(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        <div className="flex gap-2 flex-wrap">
          <button
            onClick={handleAddCity}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center gap-2"
          >
            <Plus size={16} />
            Agregar Ubicación
          </button>
          <p className="text-sm text-gray-600 flex items-center">
            💡 Haz clic en el mapa para capturar coordenadas o busca una ciudad
          </p>
        </div>
      </div>

      {/* Mapa */}
      <div className="border border-gray-300 rounded-lg shadow-md overflow-hidden">
        <MapView
          initialCenter={{ lat: 4.5709, lng: -74.2973 }}
          initialZoom={4}
          onMapReady={handleMapReady}
          className="w-full h-96"
        />
      </div>

      {/* Lista de ciudades */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h4 className="font-semibold text-gray-900 mb-4">Ciudades Cargadas ({cities.length})</h4>

        {cities.length === 0 ? (
          <p className="text-gray-500 text-center py-8">No hay ciudades cargadas. Busca una ubicación o haz clic en el mapa.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {cities.map(city => (
              <div
                key={city.id}
                className={`border rounded-lg p-4 cursor-pointer transition-all ${
                  selectedMarker?.id === city.id
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => handleZoomToCity(city)}
              >
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <h5 className="font-semibold text-gray-900">{city.name}</h5>
                    <p className="text-sm text-gray-600">{city.country}</p>
                  </div>
                  <div className="flex gap-2">
                    <span className={`px-2 py-1 text-xs rounded-full font-medium ${
                      city.hasEPW
                        ? 'bg-green-100 text-green-800'
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {city.hasEPW ? '✓ EPW' : '✗ EPW'}
                    </span>
                    {onDeleteCity && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onDeleteCity(city.id);
                          toast.success('Ciudad eliminada');
                        }}
                        className="p-1 text-red-600 hover:bg-red-50 rounded transition-colors"
                      >
                        <Trash2 size={16} />
                      </button>
                    )}
                  </div>
                </div>

                <div className="space-y-1 text-xs text-gray-600">
                  <p>
                    <strong>Latitud:</strong> {city.latitude.toFixed(4)}°
                  </p>
                  <p>
                    <strong>Longitud:</strong> {city.longitude.toFixed(4)}°
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm text-blue-900">
        <p><strong>💡 Cómo usar el buscador:</strong></p>
        <ul className="list-disc list-inside mt-2 space-y-1">
          <li>Busca por ciudad: <em>"Bogotá"</em>, <em>"Medellín, Colombia"</em></li>
          <li>Busca por dirección: <em>"Calle 5 #10-20, Bogotá"</em></li>
          <li>Haz clic en el mapa para capturar coordenadas manualmente</li>
          <li>Ingresa latitud/longitud manualmente si lo prefieres</li>
        </ul>
      </div>
    </div>
  );
}
