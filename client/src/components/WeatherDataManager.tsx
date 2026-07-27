import { useState, useRef, useEffect } from 'react';
import { Upload, Cloud, Droplets, Wind, Sun, Trash2, Download, MapPin, Calendar, CheckCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';
import { parseEPW, EPWData, getMonthlyWeatherSummary } from '@/lib/epwParser';

const MONTHS = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];

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

interface WeatherDataManagerProps {
  onWeatherDataLoaded: (data: EPWData) => void;
  weatherData: EPWData | null;
}

const STORAGE_KEY = 'weatherLibraryCities';

export default function WeatherDataManager({ onWeatherDataLoaded, weatherData }: WeatherDataManagerProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [cities, setCities] = useState<CityCard[]>([]);
  const [activeCityId, setActiveCityId] = useState<string | null>(null);

  // Cargar biblioteca desde localStorage al montar
  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed: CityCard[] = JSON.parse(saved);
        setCities(parsed);
        // Si hay una ciudad activa guardada, restaurarla
        const activeId = localStorage.getItem(STORAGE_KEY + '_active');
        if (activeId) {
          const activeCity = parsed.find(c => c.id === activeId);
          if (activeCity) {
            setActiveCityId(activeId);
            // Solo cargar si no hay datos meteorológicos ya cargados
            if (!weatherData) {
              onWeatherDataLoaded(activeCity.epwData);
            }
          }
        }
      }
    } catch (error) {
      console.error('Error loading weather library:', error);
    }
  }, []); // Solo al montar

  // Guardar biblioteca en localStorage cuando cambia
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(cities));
    } catch (error) {
      console.error('Error saving weather library:', error);
    }
  }, [cities]);

  // Guardar ciudad activa
  useEffect(() => {
    if (activeCityId) {
      localStorage.setItem(STORAGE_KEY + '_active', activeCityId);
    }
  }, [activeCityId]);

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsLoading(true);
    const reader = new FileReader();

    reader.onload = (e) => {
      try {
        const content = e.target?.result as string;
        const epwData = parseEPW(content);

        // Crear tarjeta de ciudad
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

        // Verificar si ya existe una ciudad con el mismo nombre
        const existingIdx = cities.findIndex(
          c => c.cityName.toLowerCase() === newCity.cityName.toLowerCase() &&
               c.country.toLowerCase() === newCity.country.toLowerCase()
        );

        let updatedCities: CityCard[];
        if (existingIdx >= 0) {
          // Reemplazar la existente
          updatedCities = [...cities];
          updatedCities[existingIdx] = newCity;
          toast.success(`Datos de ${newCity.cityName} actualizados en la biblioteca`);
        } else {
          updatedCities = [...cities, newCity];
          toast.success(`${newCity.cityName} agregada a la biblioteca`);
        }

        setCities(updatedCities);
        setActiveCityId(newCity.id);
        onWeatherDataLoaded(epwData);
      } catch (error) {
        toast.error('Error al procesar archivo EPW');
        console.error(error);
      } finally {
        setIsLoading(false);
      }
    };

    reader.readAsText(file);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const selectCity = (city: CityCard) => {
    setActiveCityId(city.id);
    onWeatherDataLoaded(city.epwData);
    toast.success(`Ciudad activa: ${city.cityName}`);
  };

  const deleteCity = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const city = cities.find(c => c.id === id);
    setCities(cities.filter(c => c.id !== id));
    if (activeCityId === id) {
      setActiveCityId(null);
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

  return (
    <div className="space-y-6">
      {/* Sección de carga de EPW */}
      <div className="bg-gradient-to-r from-blue-50 to-cyan-50 border border-blue-200 rounded-lg p-6">
        <div className="flex items-center gap-4 mb-4">
          <Cloud className="text-blue-600 shrink-0" size={32} />
          <div className="flex-1">
            <h3 className="font-semibold text-gray-900 mb-1">Datos Meteorológicos (EPW)</h3>
            <p className="text-sm text-gray-600">
              Carga archivos EPW de diferentes ciudades. Los datos se guardan en tu navegador para acceso rápido.
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
            className="bg-blue-600 hover:bg-blue-700 text-white whitespace-nowrap"
          >
            <Upload size={16} className="mr-2" />
            {isLoading ? 'Cargando...' : 'Cargar EPW'}
          </Button>
        </div>

        <div className="text-xs text-gray-600 bg-white/60 rounded p-3 border border-blue-100">
          <p><strong>¿Dónde descargar archivos EPW?</strong></p>
          <ul className="list-disc list-inside mt-1 space-y-0.5">
            <li><a href="https://energyplus.net/weather" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">EnergyPlus Weather Data</a></li>
            <li><a href="https://www.meteoblue.com/en/weather/archive" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">Meteoblue Archive</a></li>
            <li><a href="https://pvgis.ec.europa.eu/" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">PVGIS (Unión Europea)</a></li>
          </ul>
        </div>
      </div>

      {/* Biblioteca de ciudades - Tarjetas */}
      {cities.length === 0 ? (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
          <MapPin size={32} className="text-gray-400 mx-auto mb-3" />
          <p className="text-gray-600 font-medium">No hay ciudades en la biblioteca</p>
          <p className="text-sm text-gray-500 mt-1">Carga tu primer archivo EPW para comenzar</p>
        </div>
      ) : (
        <div className="space-y-4">
          <h4 className="font-semibold text-gray-900 flex items-center gap-2">
            <MapPin size={18} className="text-indigo-600" />
            Biblioteca de Ciudades
            <span className="bg-indigo-100 text-indigo-700 rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold">
              {cities.length}
            </span>
          </h4>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {cities.map(city => {
              const isActive = activeCityId === city.id;
              return (
                <div
                  key={city.id}
                  onClick={() => selectCity(city)}
                  className={`p-4 rounded-lg border-2 cursor-pointer transition-all hover:shadow-md ${
                    isActive
                      ? 'border-indigo-600 bg-indigo-50 shadow-md'
                      : 'border-gray-200 bg-white hover:border-indigo-300'
                  }`}
                >
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h5 className="font-semibold text-gray-900 flex items-center gap-2">
                        {city.cityName}
                        {isActive && <CheckCircle size={16} className="text-indigo-600" />}
                      </h5>
                      <p className="text-sm text-gray-600">{city.country}</p>
                    </div>
                    {isActive && (
                      <span className="bg-indigo-600 text-white text-xs px-2 py-1 rounded font-medium">Activa</span>
                    )}
                  </div>

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

                  <div className="flex gap-2">
                    <button
                      onClick={(e) => exportCityInfo(city, e)}
                      className="flex-1 px-2 py-1.5 text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 rounded transition-colors flex items-center justify-center gap-1"
                    >
                      <Download size={12} />
                      Exportar Info
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
              );
            })}
          </div>
        </div>
      )}

      {/* Resumen de datos activos */}
      {weatherData && (
        <div className="space-y-4">
          <div className="bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-lg p-6">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="font-semibold text-gray-900 mb-1 flex items-center gap-2">
                  <Sun size={18} className="text-amber-500" />
                  Datos Meteorológicos Activos
                </h3>
                <p className="text-sm text-gray-600">{weatherData.location.city}, {weatherData.location.country}</p>
                <p className="text-xs text-gray-500 mt-1">
                  Lat: {weatherData.location.latitude.toFixed(2)}° | Lon: {weatherData.location.longitude.toFixed(2)}° |
                  Elev: {weatherData.location.elevation.toFixed(0)}m | UTC{weatherData.location.timezone >= 0 ? '+' : ''}{weatherData.location.timezone}
                </p>
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div className="bg-white rounded p-3 border border-green-100">
                <p className="text-xs text-gray-600 mb-1">Registros</p>
                <p className="text-lg font-mono font-bold text-green-700">{weatherData.weatherData.length.toLocaleString()}</p>
              </div>
              <div className="bg-white rounded p-3 border border-green-100">
                <p className="text-xs text-gray-600 mb-1">Período</p>
                <p className="text-sm font-mono font-bold text-green-700">Año típico</p>
              </div>
              <div className="bg-white rounded p-3 border border-green-100">
                <p className="text-xs text-gray-600 mb-1">Zona Horaria</p>
                <p className="text-lg font-mono font-bold text-green-700">UTC{weatherData.location.timezone > 0 ? '+' : ''}{weatherData.location.timezone}</p>
              </div>
              <div className="bg-white rounded p-3 border border-green-100">
                <p className="text-xs text-gray-600 mb-1">Resolución</p>
                <p className="text-sm font-mono font-bold text-green-700">Horaria</p>
              </div>
            </div>
          </div>

          {/* Resumen mensual */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
            {MONTHS.map((month, idx) => {
              const summary = getMonthlyWeatherSummary(weatherData, idx + 1);
              return (
                <div key={month} className="bg-white border border-gray-200 rounded-lg p-3 hover:shadow-md transition-shadow">
                  <h4 className="font-semibold text-gray-900 mb-2 text-sm">{month}</h4>
                  <div className="space-y-1.5 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="text-gray-600">Temp:</span>
                      <span className="font-mono font-semibold text-gray-900">{summary.avgTemp.toFixed(1)}°C</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-gray-600 flex items-center gap-1">
                        <Sun size={10} className="text-yellow-500" />
                        Irrad:
                      </span>
                      <span className="font-mono font-semibold text-gray-900">{summary.avgIrradiance.toFixed(0)} W/m²</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-gray-600 flex items-center gap-1">
                        <Droplets size={10} className="text-blue-500" />
                        Hum:
                      </span>
                      <span className="font-mono font-semibold text-gray-900">{summary.avgHumidity.toFixed(0)}%</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-gray-600 flex items-center gap-1">
                        <Cloud size={10} className="text-gray-400" />
                        Nub:
                      </span>
                      <span className="font-mono font-semibold text-gray-900">{(summary.avgCloudCover / 10 * 100).toFixed(0)}%</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-gray-600 flex items-center gap-1">
                        <Wind size={10} className="text-cyan-500" />
                        Viento:
                      </span>
                      <span className="font-mono font-semibold text-gray-900">{summary.avgWindSpeed.toFixed(1)} m/s</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Consejo */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm text-blue-900">
        <p><strong>Consejo:</strong> Los datos se guardan en tu navegador (localStorage). Para cambiar de ciudad activa, haz clic en su tarjeta. La tarjeta activa se resalta con borde azul y la etiqueta "Activa". Para agregar más ciudades, carga nuevos archivos EPW.</p>
      </div>

      {/* Cómo se usan los datos */}
      {weatherData && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
          <h4 className="font-semibold text-gray-900 mb-2 text-sm">Cómo se usan estos datos:</h4>
          <ul className="text-sm text-gray-700 space-y-1 list-disc list-inside">
            <li><strong>Irradiancia:</strong> Ajusta automáticamente la radiación solar según nubosidad</li>
            <li><strong>Temperatura:</strong> Afecta la eficiencia del panel fotovoltaico</li>
            <li><strong>Humedad:</strong> Influye en la difusión de la luz solar</li>
            <li><strong>Nubosidad:</strong> Reduce la radiación directa disponible</li>
            <li><strong>Viento:</strong> Ayuda a enfriar los paneles mejorando eficiencia</li>
          </ul>
        </div>
      )}
    </div>
  );
}
