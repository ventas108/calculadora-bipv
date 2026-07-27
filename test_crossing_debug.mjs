import { executeCrossing, DEFAULT_CROSSING_CONFIG } from './client/src/lib/shadingMaskCrossing.ts';
import { calculateSolarPosition } from './client/src/lib/solarPosition.ts';

// Simulate a minimal EPW data structure for Medellín
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

// Generate fake weather data for critical days
const criticalDays = [
  { month: 6, day: 21 },
  { month: 12, day: 21 },
  { month: 3, day: 21 },
  { month: 9, day: 21 },
];

for (const cd of criticalDays) {
  for (let hour = 1; hour <= 24; hour++) {
    fakeEPWData.weatherData.push({
      month: cd.month,
      day: cd.day,
      hour: hour,
      dryBulbTemp: 22,
      dewPointTemp: 15,
      relativeHumidity: 70,
      atmosphericPressure: 101325,
      globalHorizontalRadiation: hour >= 7 && hour <= 18 ? 500 : 0,
      directNormalRadiation: hour >= 7 && hour <= 18 ? 400 : 0,
      diffuseHorizontalRadiation: hour >= 7 && hour <= 18 ? 200 : 0,
      windSpeed: 2,
      windDirection: 180,
      totalSkyCover: 5,
      opaqueSkyCover: 3,
    });
  }
}

// Test with no obstacles and default facades
const config = {
  ...DEFAULT_CROSSING_CONFIG,
  elevation: 1495,
};

console.log('=== Testing executeCrossing ===');
console.log('Location: Medellín (6.25°N, -75.56°W)');
console.log('Facades:', config.facades.map(f => `${f.name} (az=${f.azimuthNormal}°, tilt=${f.tilt}°)`));
console.log('Critical days:', config.criticalDays.map(d => d.name));
console.log('Hour range:', config.hourRange);
console.log('Weather data records:', fakeEPWData.weatherData.length);
console.log('');

// First, check solar positions for a critical day
console.log('--- Solar positions for Jun 21 ---');
for (let h = 6; h <= 18; h++) {
  const pos = calculateSolarPosition(6.25, -75.56, -5, 6, 21, h + 0.5);
  console.log(`  ${h}:30 → alt=${pos.altitude.toFixed(1)}°, az=${pos.azimuth.toFixed(1)}°`);
}
console.log('');

// Now test the crossing
const results = executeCrossing(fakeEPWData, [], config);
console.log(`Results: ${results.length} points generated`);

if (results.length > 0) {
  console.log('First 5 results:');
  results.slice(0, 5).forEach(r => {
    console.log(`  ${r.evento} ${r.hourStr} ${r.facade} alt=${r.heightSolar}° az=${r.azimuthSolar}° FS=${r.fs}`);
  });
} else {
  console.log('NO RESULTS! Debugging...');
  
  // Check if isFacadeExposed works
  console.log('');
  console.log('--- Checking isFacadeExposed for each facade at Jun 21 12:30 ---');
  const pos = calculateSolarPosition(6.25, -75.56, -5, 6, 21, 12.5);
  console.log(`Solar position: alt=${pos.altitude.toFixed(1)}°, az=${pos.azimuth.toFixed(1)}°`);
  
  for (const facade of config.facades) {
    const { isFacadeExposed } = await import('./client/src/lib/shadingMaskCrossing.ts');
    const exposed = isFacadeExposed(pos.altitude, pos.azimuth, facade.azimuthNormal, facade.tilt);
    console.log(`  ${facade.name} (az=${facade.azimuthNormal}°, tilt=${facade.tilt}°): exposed=${exposed}`);
  }
}
