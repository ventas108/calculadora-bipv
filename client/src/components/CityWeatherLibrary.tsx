import { useState, useRef, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Upload, Trash2, Download, MapPin, Calendar, CheckCircle, Search, Globe, Thermometer, Sun, Droplets, Wind, Cloud, ArrowRight } from 'lucide-react';
import { toast } from 'sonner';
import { parseEPW, EPWData, getMonthlyWeatherSummary } from '@/lib/epwParser';

interface CityCard {
  id: string;
  cityName: string;
  country: string;
  latitude: number;
  longitude: number;
  elevation: number;
  timezone: number;
  uploadDate: string;
  recordCount: number;
  epwData: EPWData;
}

// Shared localStorage key — same as WeatherDataManager
const STORAGE_KEY = 'weatherLibraryCities';
const ACTIVE_KEY = STORAGE_KEY + '_active';

interface CityWeatherLibraryProps {
  onSelectCity: (cityData: { id: string; cityName: string; country: string; latitude: number; longitude: number; elevation: number; uploadDate: string; epwData: EPWData }) => void;
  selectedCityId: string | null;
}

const MONTHS = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];

const REGION_COLORS: Record<string, string> = {
  'Caribe': 'bg-orange-100 text-orange-800 border-orange-300',
  'Andina': 'bg-green-100 text-green-800 border-green-300',
  'Pacífica': 'bg-blue-100 text-blue-800 border-blue-300',
  'Orinoquía': 'bg-yellow-100 text-yellow-800 border-yellow-300',
  'Amazonía': 'bg-emerald-100 text-emerald-800 border-emerald-300',
  'Insular': 'bg-cyan-100 text-cyan-800 border-cyan-300',
};

function detectRegion(lat: number, lon: number): string {
  // Simplified region detection for Colombia based on lat/lon
  if (lat > 12 || (lat > 8 && lon > -77 && lon < -71)) return 'Insular';
  if (lat > 7 && lon > -77 && lon < -74) return 'Caribe';
  if (lat > 1 && lat < 8 && lon > -77.5 && lon < -75.5) return 'Pacífica';
  if (lat > 2 && lat < 8 && lon < -69) return 'Orinoquía';
  if (lat < 2 && lon < -69) return 'Amazonía';
  if (lat > 1 && lat < 8 && lon > -77 && lon < -73) return 'Andina';
  // Default based on elevation hints
  return 'Andina';
}

export default function CityWeatherLibrary({ onSelectCity, selectedCityId }: CityWeatherLibraryProps) {
  const [cities, setCities] = useState<CityCard[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedCityId, setExpandedCityId] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load library from shared localStorage
  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed: CityCard[] = JSON.parse(saved);
        setCities(parsed);
      }
    } catch (error) {
      console.error('Error loading weather library:', error);
    }
  }, []);

  // Save library to shared localStorage when it changes
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(cities));
    } catch (error) {
      console.error('Error saving weather library:', error);
    }
  }, [cities]);

  // Listen for storage changes from other tabs or WeatherDataManager
  useEffect(() => {
    const handleStorage = (e: StorageEvent) => {
      if (e.key === STORAGE_KEY && e.newValue) {
        try {
          setCities(JSON.parse(e.newValue));
        } catch {}
      }
    };
    window.addEventListener('storage', handleStorage);
    return () => window.removeEventListener('storage', handleStorage);
  }, []);

  const handleFileUpload = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsLoading(true);
    const reader = new FileReader();

    reader.onload = (e) => {
      try {
        const content = e.target?.result as string;
        const epwData = parseEPW(content);

        const newCity: CityCard = {
          id: Date.now().toString(),
          cityName: epwData.location.city,
          country: epwData.location.country,
          latitude: epwData.location.latitude,
          longitude: epwData.location.longitude,
          elevation: epwData.location.elevation,
          timezone: epwData.location.timezone,
          uploadDate: new Date().toLocaleDateString('es-ES'),
          recordCount: epwData.weatherData.length,
          epwData,
        };

        // Check for duplicate city
        const existingIdx = cities.findIndex(
          c => c.cityName.toLowerCase() === newCity.cityName.toLowerCase() &&
               c.country.toLowerCase() === newCity.country.toLowerCase()
        );

        let updatedCities: CityCard[];
        if (existingIdx >= 0) {
          updatedCities = [...cities];
          updatedCities[existingIdx] = newCity;
          toast.success(`Datos de ${newCity.cityName} actualizados en la biblioteca`);
        } else {
          updatedCities = [...cities, newCity];
          toast.success(`${newCity.cityName} agregada a la biblioteca`);
        }

        setCities(updatedCities);
        // Save active city ID
        localStorage.setItem(ACTIVE_KEY, newCity.id);
        // Notify parent
        onSelectCity({
          id: newCity.id,
          cityName: newCity.cityName,
          country: newCity.country,
          latitude: newCity.latitude,
          longitude: newCity.longitude,
          elevation: newCity.elevation,
          uploadDate: newCity.uploadDate,
          epwData: newCity.epwData,
        });
      } catch (error) {
        toast.error('Error al procesar archivo EPW. Verifica que el archivo sea válido.');
        console.error(error);
      } finally {
        setIsLoading(false);
      }
    };

    reader.readAsText(file);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, [cities, onSelectCity]);

  const selectCity = (city: CityCard) => {
    localStorage.setItem(ACTIVE_KEY, city.id);
    onSelectCity({
      id: city.id,
      cityName: city.cityName,
      country: city.country,
      latitude: city.latitude,
      longitude: city.longitude,
      elevation: city.elevation,
      uploadDate: city.uploadDate,
      epwData: city.epwData,
    });
    toast.success(`Ciudad activa: ${city.cityName} — Datos meteorológicos cargados`);
  };

  const deleteCity = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const city = cities.find(c => c.id === id);
    setCities(cities.filter(c => c.id !== id));
    if (selectedCityId === id) {
      localStorage.removeItem(ACTIVE_KEY);
    }
    toast.success(`${city?.cityName || 'Ciudad'} eliminada de la biblioteca`);
  };

  const exportCityInfo = (city: CityCard, e: React.MouseEvent) => {
    e.stopPropagation();
    const data = {
      ciudad: city.cityName,
      pais: city.country,
      latitud: city.latitude,
      longitud: city.longitude,
      elevacion: city.elevation,
      zonaHoraria: city.timezone,
      fechaCarga: city.uploadDate,
      registros: city.recordCount,
    };
    const json = JSON.stringify(data, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${city.cityName.replace(/\s+/g, '_')}_info.json`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  const toggleExpand = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setExpandedCityId(expandedCityId === id ? null : id);
  };

  // Filter cities by search term
  const filteredCities = cities.filter(c =>
    searchTerm === '' ||
    c.cityName.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.country.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header with upload */}
      <div className="bg-gradient-to-r from-indigo-50 to-purple-50 border border-indigo-200 rounded-lg p-6">
        <div className="flex items-center gap-4 mb-4">
          <Globe className="text-indigo-600 shrink-0" size={32} />
          <div className="flex-1">
            <h3 className="font-semibold text-gray-900 mb-1">Biblioteca de Ciudades</h3>
            <p className="text-sm text-gray-600">
              Gestiona tu colección de datos meteorológicos EPW. Carga archivos de diferentes ciudades,
              compara sus datos y selecciona la ciudad activa para los cálculos.
            </p>
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept=".epw"
            onChange={handleFileUpload}
            className="hidden"
            disabled={isLoading}
          />
          <Button
            onClick={() => fileInputRef.current?.click()}
            disabled={isLoading}
            className="bg-indigo-600 hover:bg-indigo-700 text-white whitespace-nowrap"
          >
            <Upload size={16} className="mr-2" />
            {isLoading ? 'Procesando...' : 'Cargar EPW'}
          </Button>
        </div>

        {/* Drag and drop area */}
        <label className="flex items-center justify-center w-full p-6 border-2 border-dashed border-indigo-300 rounded-lg cursor-pointer hover:bg-indigo-50/50 transition-colors mb-4">
          <div className="flex flex-col items-center">
            <Upload size={28} className="text-indigo-500 mb-2" />
            <span className="text-sm font-medium text-gray-700">Arrastra un archivo EPW aquí o haz clic para seleccionar</span>
            <span className="text-xs text-gray-500 mt-1">Archivos .epw de EnergyPlus Weather</span>
          </div>
          <input
            type="file"
            accept=".epw"
            onChange={handleFileUpload}
            disabled={isLoading}
            className="hidden"
          />
        </label>

        <div className="text-xs text-gray-600 bg-white/60 rounded p-3 border border-indigo-100">
          <p><strong>¿Dónde descargar archivos EPW?</strong></p>
          <ul className="list-disc list-inside mt-1 space-y-0.5">
            <li><a href="https://energyplus.net/weather" target="_blank" rel="noopener noreferrer" className="text-indigo-600 hover:underline">EnergyPlus Weather Data</a> — Base de datos oficial</li>
            <li><a href="https://www.meteoblue.com/en/weather/archive" target="_blank" rel="noopener noreferrer" className="text-indigo-600 hover:underline">Meteoblue Archive</a> — Datos históricos</li>
            <li><a href="https://pvgis.ec.europa.eu/" target="_blank" rel="noopener noreferrer" className="text-indigo-600 hover:underline">PVGIS (Unión Europea)</a> — Datos de radiación solar</li>
          </ul>
        </div>
      </div>

      {/* Search bar (only show if there are cities) */}
      {cities.length > 0 && (
        <div className="relative">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder="Buscar ciudad o país..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          />
          {searchTerm && (
            <button
              onClick={() => setSearchTerm('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          )}
        </div>
      )}

      {/* City cards */}
      {cities.length === 0 ? (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-10 text-center">
          <MapPin size={40} className="text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600 font-semibold text-lg">No hay ciudades en la biblioteca</p>
          <p className="text-sm text-gray-500 mt-2 mb-4">Carga tu primer archivo EPW para comenzar a analizar datos meteorológicos</p>
          <Button
            onClick={() => fileInputRef.current?.click()}
            className="bg-indigo-600 hover:bg-indigo-700 text-white"
          >
            <Upload size={16} className="mr-2" />
            Cargar primer EPW
          </Button>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="font-semibold text-gray-900 flex items-center gap-2">
              <MapPin size={18} className="text-indigo-600" />
              Ciudades Cargadas
              <span className="bg-indigo-100 text-indigo-700 rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold">
                {filteredCities.length}
              </span>
              {searchTerm && filteredCities.length !== cities.length && (
                <span className="text-xs text-gray-500 font-normal">de {cities.length} total</span>
              )}
            </h4>
          </div>

          {filteredCities.length === 0 && searchTerm ? (
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-6 text-center">
              <Search size={24} className="text-gray-400 mx-auto mb-2" />
              <p className="text-gray-600">No se encontraron ciudades para "{searchTerm}"</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredCities.map(city => {
                const isActive = selectedCityId === city.id;
                const isExpanded = expandedCityId === city.id;
                const region = detectRegion(city.latitude, city.longitude);
                const regionStyle = REGION_COLORS[region] || 'bg-gray-100 text-gray-800 border-gray-300';

                return (
                  <div
                    key={city.id}
                    onClick={() => selectCity(city)}
                    className={`rounded-lg border-2 cursor-pointer transition-all hover:shadow-lg ${
                      isActive
                        ? 'border-indigo-600 bg-indigo-50/50 shadow-lg ring-2 ring-indigo-200'
                        : 'border-gray-200 bg-white hover:border-indigo-300'
                    }`}
                  >
                    <div className="p-4">
                      {/* City header */}
                      <div className="flex justify-between items-start mb-3">
                        <div className="flex-1 min-w-0">
                          <h5 className="font-semibold text-gray-900 flex items-center gap-2 truncate">
                            {city.cityName}
                            {isActive && <CheckCircle size={16} className="text-indigo-600 shrink-0" />}
                          </h5>
                          <div className="flex items-center gap-2 mt-1">
                            <span className="text-sm text-gray-600">{city.country}</span>
                            <span className={`text-[10px] px-1.5 py-0.5 rounded border font-medium ${regionStyle}`}>
                              {region}
                            </span>
                          </div>
                        </div>
                        {isActive && (
                          <span className="bg-indigo-600 text-white text-xs px-2 py-1 rounded font-medium shrink-0 ml-2">Activa</span>
                        )}
                      </div>

                      {/* Key data grid */}
                      <div className="grid grid-cols-2 gap-2 text-xs mb-3">
                        <div className="bg-gray-50 rounded p-2">
                          <p className="text-gray-500">Latitud</p>
                          <p className="font-mono font-semibold text-gray-900">{city.latitude.toFixed(2)}°</p>
                        </div>
                        <div className="bg-gray-50 rounded p-2">
                          <p className="text-gray-500">Longitud</p>
                          <p className="font-mono font-semibold text-gray-900">{city.longitude.toFixed(2)}°</p>
                        </div>
                        <div className="bg-gray-50 rounded p-2">
                          <p className="text-gray-500">Elevación</p>
                          <p className="font-mono font-semibold text-gray-900">{city.elevation.toFixed(0)} m</p>
                        </div>
                        <div className="bg-gray-50 rounded p-2">
                          <p className="text-gray-500">Zona Horaria</p>
                          <p className="font-mono font-semibold text-gray-900">UTC{city.timezone >= 0 ? '+' : ''}{city.timezone}</p>
                        </div>
                        <div className="bg-gray-50 rounded p-2">
                          <p className="text-gray-500">Registros</p>
                          <p className="font-mono font-semibold text-gray-900">{city.recordCount.toLocaleString()}</p>
                        </div>
                        <div className="bg-gray-50 rounded p-2">
                          <p className="text-gray-500 flex items-center gap-1"><Calendar size={10} /> Cargado</p>
                          <p className="font-mono font-semibold text-gray-900 text-[11px]">{city.uploadDate}</p>
                        </div>
                      </div>

                      {/* Expand button for monthly data */}
                      <button
                        onClick={(e) => toggleExpand(city.id, e)}
                        className="w-full text-xs text-indigo-600 hover:text-indigo-800 font-medium py-1.5 rounded hover:bg-indigo-50 transition-colors flex items-center justify-center gap-1"
                      >
                        <ArrowRight size={12} className={`transition-transform ${isExpanded ? 'rotate-90' : ''}`} />
                        {isExpanded ? 'Ocultar resumen mensual' : 'Ver resumen mensual'}
                      </button>

                      {/* Expanded monthly summary */}
                      {isExpanded && (
                        <div className="mt-3 pt-3 border-t border-gray-200">
                          <div className="grid grid-cols-3 gap-1.5">
                            {MONTHS.map((month, idx) => {
                              const summary = getMonthlyWeatherSummary(city.epwData, idx + 1);
                              return (
                                <div key={month} className="bg-gray-50 rounded p-1.5 text-[10px]">
                                  <p className="font-semibold text-gray-900 mb-0.5">{month}</p>
                                  <div className="space-y-0.5 text-gray-600">
                                    <div className="flex items-center gap-0.5">
                                      <Thermometer size={8} className="text-red-400" />
                                      <span>{summary.avgTemp.toFixed(1)}°C</span>
                                    </div>
                                    <div className="flex items-center gap-0.5">
                                      <Sun size={8} className="text-yellow-500" />
                                      <span>{summary.avgIrradiance.toFixed(0)} W/m²</span>
                                    </div>
                                    <div className="flex items-center gap-0.5">
                                      <Droplets size={8} className="text-blue-400" />
                                      <span>{summary.avgHumidity.toFixed(0)}%</span>
                                    </div>
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      )}

                      {/* Action buttons */}
                      <div className="flex gap-2 mt-3">
                        {!isActive && (
                          <button
                            onClick={(e) => { e.stopPropagation(); selectCity(city); }}
                            className="flex-1 px-2 py-1.5 text-xs bg-indigo-100 hover:bg-indigo-200 text-indigo-700 rounded transition-colors flex items-center justify-center gap-1 font-medium"
                          >
                            <CheckCircle size={12} />
                            Activar
                          </button>
                        )}
                        <button
                          onClick={(e) => exportCityInfo(city, e)}
                          className="flex-1 px-2 py-1.5 text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 rounded transition-colors flex items-center justify-center gap-1"
                        >
                          <Download size={12} />
                          Exportar
                        </button>
                        <button
                          onClick={(e) => deleteCity(city.id, e)}
                          className="flex-1 px-2 py-1.5 text-xs bg-red-50 hover:bg-red-100 text-red-700 rounded transition-colors flex items-center justify-center gap-1"
                        >
                          <Trash2 size={12} />
                          Eliminar
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Tips */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm text-blue-900">
        <p><strong>Cómo funciona:</strong></p>
        <ul className="list-disc list-inside mt-2 space-y-1 text-xs">
          <li><strong>Cargar:</strong> Haz clic en "Cargar EPW" o arrastra un archivo .epw al área de carga</li>
          <li><strong>Activar:</strong> Haz clic en la tarjeta de una ciudad para activarla como fuente de datos meteorológicos</li>
          <li><strong>Sincronización:</strong> La ciudad activa se usa automáticamente en la Calculadora, Simulador Energía, Radiación Solar y demás herramientas</li>
          <li><strong>Persistencia:</strong> Los datos se guardan en tu navegador (localStorage) y persisten entre sesiones</li>
          <li><strong>Región:</strong> La región climática colombiana se detecta automáticamente según la ubicación</li>
        </ul>
      </div>
    </div>
  );
}
