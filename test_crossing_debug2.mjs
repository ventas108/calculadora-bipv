import { executeCrossing, calculateFSClimatico, DEFAULT_CROSSING_CONFIG } from './client/src/lib/shadingMaskCrossing.ts';
import { calculateSolarPosition } from './client/src/lib/solarPosition.ts';

// The WeatherData interface uses:
// directNormalIrradiance, diffuseHorizontalIrradiance, globalHorizontalIrradiance
// NOT directNormalRadiation etc.

const fakeEPWData = {
  location: {
    city: 'Medellin',
    latitude: 6.25,
    longitude: -75.56,
    timezone: -5,
    elevation: 1495,
  },
  weatherData: [],
};

const criticalDays = [
  { month: 6, day: 21 },
  { month: 12, day: 21 },
  { month: 3, day: 21 },
  { month: 9, day: 21 },
];

for (const cd of criticalDays) {
  for (let hour = 1; hour <= 24; hour++) {
    fakeEPWData.weatherData.push({
      year: 2023,
      month: cd.month,
      day: cd.day,
      hour: hour,
      minute: 0,
      temperature: 22,
      dewPoint: 15,
      relativeHumidity: 70,
      atmosphericPressure: 101325,
      globalHorizontalIrradiance: hour >= 7 && hour <= 18 ? 500 : 0,
      directNormalIrradiance: hour >= 7 && hour <= 18 ? 400 : 0,
      diffuseHorizontalIrradiance: hour >= 7 && hour <= 18 ? 200 : 0,
      windSpeed: 2,
      cloudCover: 5,
    });
  }
}

console.log('=== Testing with CORRECT field names ===');
console.log('Weather record sample:', JSON.stringify(fakeEPWData.weatherData[7], null, 2));

// Test calculateFSClimatico directly
const pos = calculateSolarPosition(6.25, -75.56, -5, 6, 21, 12.5);
const weatherRec = fakeEPWData.weatherData.find(w => w.month === 6 && w.day === 21 && w.hour === 13);
console.log('\nWeather record for Jun 21 13:00:', weatherRec);
console.log('Solar pos:', pos);

const fsClim = calculateFSClimatico(weatherRec, pos.altitude, pos.azimuth, 0, 90, 0.2, 1495);
console.log('FS Climático:', fsClim);

// Now test full crossing
const config = { ...DEFAULT_CROSSING_CONFIG, elevation: 1495 };
const results = executeCrossing(fakeEPWData, [], config);
console.log(`\nResults: ${results.length} points generated`);
if (results.length > 0) {
  console.log('First 3:', results.slice(0, 3).map(r => `${r.evento} ${r.hourStr} ${r.facade} FS=${r.fs}`));
  const nanCount = results.filter(r => isNaN(r.fs)).length;
  console.log(`NaN count: ${nanCount} / ${results.length}`);
}
