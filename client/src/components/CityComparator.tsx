import { useState, useMemo } from 'react';
import { EPWData, getMonthlyWeatherSummary } from '@/lib/epwParser';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from 'recharts';
import { Zap, Cloud, Droplets, Wind, Sun } from 'lucide-react';

const MONTHS = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];

interface CityData {
  id: string;
  name: string;
  country: string;
  latitude: number;
  longitude: number;
  epwData: EPWData;
}

interface CityComparatorProps {
  cities: CityData[];
}

export default function CityComparator({ cities }: CityComparatorProps) {
  const [selectedCities, setSelectedCities] = useState<string[]>(cities.slice(0, 2).map(c => c.id));

  const comparativeData = useMemo(() => {
    const data = MONTHS.map((month, idx) => {
      const result: any = { month };

      selectedCities.forEach(cityId => {
        const city = cities.find(c => c.id === cityId);
        if (city) {
          const summary = getMonthlyWeatherSummary(city.epwData, idx + 1);
          result[`${city.name}_temp`] = Math.round(summary.avgTemp);
          result[`${city.name}_irr`] = Math.round(summary.avgIrradiance);
          result[`${city.name}_humidity`] = Math.round(summary.avgHumidity);
        }
      });

      return result;
    });

    return data;
  }, [selectedCities, cities]);

  const stats = useMemo(() => {
    const statsMap: any = {};

    selectedCities.forEach(cityId => {
      const city = cities.find(c => c.id === cityId);
      if (city) {
        const temps: number[] = [];
        const irradiances: number[] = [];
        const humidities: number[] = [];
        const windSpeeds: number[] = [];

        for (let month = 1; month <= 12; month++) {
          const summary = getMonthlyWeatherSummary(city.epwData, month);
          temps.push(summary.avgTemp);
          irradiances.push(summary.avgIrradiance);
          humidities.push(summary.avgHumidity);
          windSpeeds.push(summary.avgWindSpeed);
        }

        statsMap[city.id] = {
          name: city.name,
          avgTemp: (temps.reduce((a, b) => a + b) / temps.length).toFixed(1),
          maxTemp: Math.max(...temps).toFixed(1),
          minTemp: Math.min(...temps).toFixed(1),
          avgIrradiance: Math.round(irradiances.reduce((a, b) => a + b) / irradiances.length),
          maxIrradiance: Math.round(Math.max(...irradiances)),
          avgHumidity: Math.round(humidities.reduce((a, b) => a + b) / humidities.length),
          avgWindSpeed: (windSpeeds.reduce((a, b) => a + b) / windSpeeds.length).toFixed(1),
        };
      }
    });

    return statsMap;
  }, [selectedCities, cities]);

  const toggleCity = (cityId: string) => {
    if (selectedCities.includes(cityId)) {
      if (selectedCities.length > 1) {
        setSelectedCities(selectedCities.filter(id => id !== cityId));
      }
    } else {
      if (selectedCities.length < 3) {
        setSelectedCities([...selectedCities, cityId]);
      }
    }
  };

  const colors = ['#3B82F6', '#EF4444', '#10B981'];

  return (
    <div className="space-y-6">
      <div className="bg-gradient-to-r from-blue-50 to-cyan-50 border border-blue-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Comparador de Ciudades</h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
          {cities.map(city => (
            <button
              key={city.id}
              onClick={() => toggleCity(city.id)}
              className={`p-3 rounded-lg border-2 transition-all text-left ${
                selectedCities.includes(city.id)
                  ? 'border-blue-600 bg-blue-100'
                  : 'border-gray-200 bg-white hover:border-blue-300'
              }`}
            >
              <p className="font-semibold text-gray-900">{city.name}</p>
              <p className="text-sm text-gray-600">{city.country}</p>
              <p className="text-xs text-gray-500 mt-1">{city.latitude.toFixed(2)}°, {city.longitude.toFixed(2)}°</p>
            </button>
          ))}
        </div>

        <p className="text-xs text-gray-600 bg-blue-100 rounded p-2">
          Selecciona 2-3 ciudades para comparar. Puedes cambiar la selección en cualquier momento.
        </p>
      </div>

      {selectedCities.length > 0 && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {selectedCities.map((cityId, idx) => {
              const city = cities.find(c => c.id === cityId);
              const stat = stats[cityId];

              if (!city || !stat) return null;

              return (
                <div key={cityId} className="bg-white border border-gray-200 rounded-lg p-6">
                  <h4 className="font-semibold text-gray-900 mb-4">{city.name}, {city.country}</h4>

                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div className="bg-orange-50 rounded p-3 border border-orange-100">
                      <div className="flex items-center gap-2 mb-1">
                        <Sun size={16} className="text-orange-600" />
                        <p className="text-gray-600">Temp. Prom.</p>
                      </div>
                      <p className="text-xl font-mono font-bold text-orange-700">{stat.avgTemp}°C</p>
                      <p className="text-xs text-gray-500 mt-1">Rango: {stat.minTemp}° a {stat.maxTemp}°</p>
                    </div>

                    <div className="bg-yellow-50 rounded p-3 border border-yellow-100">
                      <div className="flex items-center gap-2 mb-1">
                        <Zap size={16} className="text-yellow-600" />
                        <p className="text-gray-600">Irradiancia</p>
                      </div>
                      <p className="text-xl font-mono font-bold text-yellow-700">{stat.avgIrradiance}</p>
                      <p className="text-xs text-gray-500 mt-1">Máx: {stat.maxIrradiance} W/m²</p>
                    </div>

                    <div className="bg-blue-50 rounded p-3 border border-blue-100">
                      <div className="flex items-center gap-2 mb-1">
                        <Droplets size={16} className="text-blue-600" />
                        <p className="text-gray-600">Humedad</p>
                      </div>
                      <p className="text-xl font-mono font-bold text-blue-700">{stat.avgHumidity}%</p>
                      <p className="text-xs text-gray-500 mt-1">Promedio anual</p>
                    </div>

                    <div className="bg-cyan-50 rounded p-3 border border-cyan-100">
                      <div className="flex items-center gap-2 mb-1">
                        <Wind size={16} className="text-cyan-600" />
                        <p className="text-gray-600">Viento</p>
                      </div>
                      <p className="text-xl font-mono font-bold text-cyan-700">{stat.avgWindSpeed}</p>
                      <p className="text-xs text-gray-500 mt-1">m/s promedio</p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h4 className="font-semibold text-gray-900 mb-4">Comparación de Temperatura Mensual</h4>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={comparativeData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis dataKey="month" stroke="#6B7280" />
                <YAxis stroke="#6B7280" label={{ value: 'Temperatura (°C)', angle: -90, position: 'insideLeft' }} />
                <Tooltip contentStyle={{ backgroundColor: '#F9FAFB', border: '1px solid #E5E7EB', borderRadius: '8px' }} />
                <Legend />
                {selectedCities.map((cityId, idx) => {
                  const city = cities.find(c => c.id === cityId);
                  return (
                    <Line
                      key={cityId}
                      type="monotone"
                      dataKey={`${city?.name}_temp`}
                      stroke={colors[idx]}
                      name={city?.name}
                      strokeWidth={2}
                      dot={{ r: 4 }}
                    />
                  );
                })}
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h4 className="font-semibold text-gray-900 mb-4">Comparación de Irradiancia Mensual</h4>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={comparativeData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis dataKey="month" stroke="#6B7280" />
                <YAxis stroke="#6B7280" label={{ value: 'Irradiancia (W/m²)', angle: -90, position: 'insideLeft' }} />
                <Tooltip contentStyle={{ backgroundColor: '#F9FAFB', border: '1px solid #E5E7EB', borderRadius: '8px' }} />
                <Legend />
                {selectedCities.map((cityId, idx) => {
                  const city = cities.find(c => c.id === cityId);
                  return (
                    <Bar
                      key={cityId}
                      dataKey={`${city?.name}_irr`}
                      fill={colors[idx]}
                      name={city?.name}
                    />
                  );
                })}
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-green-50 border border-green-200 rounded-lg p-6">
            <h4 className="font-semibold text-gray-900 mb-3">Recomendación de Ubicación</h4>
            <div className="space-y-2 text-sm text-gray-700">
              {selectedCities.length === 2 && (
                <>
                  <p>
                    <strong>Mejor para energía solar:</strong>{' '}
                    {stats[selectedCities[0]].avgIrradiance > stats[selectedCities[1]].avgIrradiance
                      ? cities.find(c => c.id === selectedCities[0])?.name
                      : cities.find(c => c.id === selectedCities[1])?.name}
                    {' '}tiene mayor irradiancia promedio.
                  </p>
                  <p>
                    <strong>Mejor para eficiencia térmica:</strong>{' '}
                    {stats[selectedCities[0]].avgTemp < stats[selectedCities[1]].avgTemp
                      ? cities.find(c => c.id === selectedCities[0])?.name
                      : cities.find(c => c.id === selectedCities[1])?.name}
                    {' '}tiene temperaturas más bajas (mejor para paneles).
                  </p>
                </>
              )}
              <p className="mt-3 text-xs text-gray-600">
                Considera también factores locales como orografía, contaminación, y disponibilidad de espacio.
              </p>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
