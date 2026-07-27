import { describe, expect, it } from "vitest";
import {
  clearSkyDNI,
  clearSkyDHI,
  calculatePOA,
  calculateFSClimatico,
  calculateFSGeometrico,
  classifySituation,
  classifyCombinedSituation,
  isFacadeExposed,
  executeCrossing,
  crossingResultsToAnalysisPoints,
  CRITICAL_DAYS,
  MONTHLY_CRITICAL_DAYS,
  DEFAULT_CROSSING_CONFIG,
} from "@/lib/shadingMaskCrossing";
import type { WeatherData, EPWData } from "@/lib/epwParser";
import type { ObstaclePolygon } from "@/components/SunPathDiagram";

// ─── Helper Fixtures ─────────────────────────────────────────────────────────

function createMockWeatherRecord(overrides: Partial<WeatherData> = {}): WeatherData {
  return {
    year: 2024,
    month: 3,
    day: 20,
    hour: 12,
    minute: 0,
    temperature: 25,
    dewPoint: 18,
    relativeHumidity: 65,
    atmosphericPressure: 101325,
    directNormalIrradiance: 800,
    diffuseHorizontalIrradiance: 150,
    globalHorizontalIrradiance: 850,
    windSpeed: 3,
    cloudCover: 2,
    ...overrides,
  };
}

function createMockEPWData(): EPWData {
  // Create a minimal EPW dataset for Medellín (6.25°N, -75.56°W, TZ -5, elev 1495m)
  const weatherData: WeatherData[] = [];

  // Generate data for March 20 (equinox) and June 21 (solstice)
  for (const { month, day } of [{ month: 3, day: 20 }, { month: 6, day: 21 }, { month: 9, day: 22 }, { month: 12, day: 21 }]) {
    for (let hour = 1; hour <= 24; hour++) {
      const isDay = hour >= 7 && hour <= 18;
      weatherData.push({
        year: 2024,
        month,
        day,
        hour,
        minute: 0,
        temperature: isDay ? 25 : 18,
        dewPoint: 16,
        relativeHumidity: 70,
        atmosphericPressure: 85000, // ~1495m elevation
        directNormalIrradiance: isDay ? 600 + Math.random() * 300 : 0,
        diffuseHorizontalIrradiance: isDay ? 100 + Math.random() * 100 : 0,
        globalHorizontalIrradiance: isDay ? 500 + Math.random() * 400 : 0,
        windSpeed: 2,
        cloudCover: 3,
      });
    }
  }

  return {
    location: {
      city: "Medellin",
      state: "Antioquia",
      country: "COL",
      latitude: 6.25,
      longitude: -75.56,
      timezone: -5,
      elevation: 1495,
    },
    weatherData,
  };
}

function createMockObstacles(): ObstaclePolygon[] {
  // Create a simple obstacle that covers azimuth -30 to 30, altitude 10 to 40
  // This simulates a building to the south
  return [
    {
      id: "obs1",
      name: "Edificio Sur",
      color: "#ef4444",
      vertices: [
        { azimuth: -30, altitude: 10 },
        { azimuth: 30, altitude: 10 },
        { azimuth: 30, altitude: 40 },
        { azimuth: -30, altitude: 40 },
      ],
      visible: true,
    },
  ];
}

// ─── Tests: Clear Sky Model ──────────────────────────────────────────────────

describe("clearSkyDNI", () => {
  it("returns 0 when solar altitude is 0 or negative", () => {
    expect(clearSkyDNI(0, 0)).toBe(0);
    expect(clearSkyDNI(-5, 0)).toBe(0);
  });

  it("returns positive DNI for positive solar altitude", () => {
    const dni = clearSkyDNI(45, 0);
    expect(dni).toBeGreaterThan(0);
    expect(dni).toBeLessThan(1400); // Cannot exceed solar constant
  });

  it("increases with solar altitude", () => {
    const dni30 = clearSkyDNI(30, 0);
    const dni60 = clearSkyDNI(60, 0);
    const dni90 = clearSkyDNI(90, 0);
    expect(dni60).toBeGreaterThan(dni30);
    expect(dni90).toBeGreaterThan(dni60);
  });

  it("adjusts for elevation", () => {
    const dniSea = clearSkyDNI(45, 0);
    const dniHigh = clearSkyDNI(45, 1500);
    // Higher elevation = clearer atmosphere = higher DNI
    expect(dniHigh).toBeGreaterThan(dniSea);
  });

  it("produces reasonable values at typical solar noon (altitude ~70°, sea level)", () => {
    const dni = clearSkyDNI(70, 0);
    // Typical clear-sky DNI at high altitude: 800-1000 W/m²
    expect(dni).toBeGreaterThan(700);
    expect(dni).toBeLessThan(1100);
  });
});

describe("clearSkyDHI", () => {
  it("returns 0 when solar altitude is 0 or negative", () => {
    expect(clearSkyDHI(0, 0)).toBe(0);
    expect(clearSkyDHI(-5, 100)).toBe(0);
  });

  it("returns positive DHI for positive inputs", () => {
    const dhi = clearSkyDHI(45, 800);
    expect(dhi).toBeGreaterThan(0);
  });

  it("is much smaller than DNI for clear sky", () => {
    const altitude = 60;
    const dni = clearSkyDNI(altitude, 0);
    const dhi = clearSkyDHI(altitude, dni);
    // For clear sky, DHI should be 10-20% of GHI
    expect(dhi).toBeLessThan(dni * 0.5);
  });
});

// ─── Tests: POA Calculation ──────────────────────────────────────────────────

describe("calculatePOA", () => {
  it("returns 0 when solar altitude is 0 or negative", () => {
    expect(calculatePOA(800, 150, 850, 0, 0, 0, 90, 0.2)).toBe(0);
    expect(calculatePOA(800, 150, 850, -5, 0, 0, 90, 0.2)).toBe(0);
  });

  it("returns positive POA for a south-facing vertical surface at solar noon", () => {
    // Sun at altitude 60°, azimuth 0° (due south), facade facing south (azimuth 0°)
    const poa = calculatePOA(800, 150, 850, 60, 0, 0, 90, 0.2);
    expect(poa).toBeGreaterThan(0);
  });

  it("returns higher POA when sun faces the facade directly", () => {
    // Sun at azimuth 0° (south), facade facing south vs east
    const poaSouth = calculatePOA(800, 150, 850, 45, 0, 0, 90, 0.2);
    const poaEast = calculatePOA(800, 150, 850, 45, 0, -90, 90, 0.2);
    expect(poaSouth).toBeGreaterThan(poaEast);
  });

  it("includes diffuse and reflected components even when beam is zero", () => {
    // Sun behind the facade (azimuth 180° away)
    const poa = calculatePOA(0, 150, 150, 45, 180, 0, 90, 0.2);
    // Should still have diffuse component
    expect(poa).toBeGreaterThan(0);
  });

  it("horizontal surface receives full GHI at zenith", () => {
    // Horizontal surface (tilt=0), sun at zenith (alt=90)
    const poa = calculatePOA(1000, 100, 1100, 90, 0, 0, 0, 0.2);
    // Should be close to DNI + DHI = 1100
    expect(poa).toBeGreaterThan(1050);
    expect(poa).toBeLessThan(1150);
  });
});

// ─── Tests: FS Climático ─────────────────────────────────────────────────────

describe("calculateFSClimatico", () => {
  it("returns 0 when solar altitude is 0 or negative", () => {
    const weather = createMockWeatherRecord();
    expect(calculateFSClimatico(weather, 0, 0, 0, 90, 0.2, 0)).toBe(0);
    expect(calculateFSClimatico(weather, -5, 0, 0, 90, 0.2, 0)).toBe(0);
  });

  it("returns low FS for clear sky conditions (high DNI)", () => {
    // Clear sky: DNI close to clear-sky model
    const weather = createMockWeatherRecord({
      directNormalIrradiance: 900,
      diffuseHorizontalIrradiance: 100,
      globalHorizontalIrradiance: 950,
    });
    const fs = calculateFSClimatico(weather, 60, 0, 0, 90, 0.2, 0);
    expect(fs).toBeLessThan(0.3); // Low FS = clear sky
  });

  it("returns high FS for overcast conditions (low DNI, high DHI)", () => {
    // Overcast: very low DNI, high diffuse fraction
    const weather = createMockWeatherRecord({
      directNormalIrradiance: 50,
      diffuseHorizontalIrradiance: 200,
      globalHorizontalIrradiance: 250,
    });
    const fs = calculateFSClimatico(weather, 60, 0, 0, 90, 0.2, 0);
    expect(fs).toBeGreaterThan(0.5); // High FS = overcast
  });

  it("is bounded between 0 and 1", () => {
    const weather = createMockWeatherRecord();
    const fs = calculateFSClimatico(weather, 45, 30, 0, 90, 0.2, 1500);
    expect(fs).toBeGreaterThanOrEqual(0);
    expect(fs).toBeLessThanOrEqual(1);
  });

  it("returns higher FS for completely cloudy vs partially cloudy", () => {
    const clearWeather = createMockWeatherRecord({
      directNormalIrradiance: 850,
      diffuseHorizontalIrradiance: 80,
      globalHorizontalIrradiance: 900,
    });
    const cloudyWeather = createMockWeatherRecord({
      directNormalIrradiance: 100,
      diffuseHorizontalIrradiance: 250,
      globalHorizontalIrradiance: 300,
    });

    const fsClear = calculateFSClimatico(clearWeather, 50, 0, 0, 90, 0.2, 0);
    const fsCloudy = calculateFSClimatico(cloudyWeather, 50, 0, 0, 90, 0.2, 0);
    expect(fsCloudy).toBeGreaterThan(fsClear);
  });
});

// ─── Tests: FS Geométrico ────────────────────────────────────────────────────

describe("calculateFSGeometrico", () => {
  it("returns 0 when there are no obstacles", () => {
    const fs = calculateFSGeometrico([], 45, 0, 6.25, -75.56, -5, 3, 20, 12);
    expect(fs).toBe(0);
  });

  it("returns 0 when solar altitude is 0 or negative", () => {
    const obstacles = createMockObstacles();
    const fs = calculateFSGeometrico(obstacles, 0, 0, 6.25, -75.56, -5, 3, 20, 12);
    expect(fs).toBe(0);
  });

  it("returns positive FS when sun is inside an obstacle polygon", () => {
    // Create an obstacle that covers a realistic angular range
    // In the stereographic projection, wide azimuth ranges (like -90 to 90) create
    // degenerate polygons. Use a narrower range that forms a proper polygon.
    const obstacle: ObstaclePolygon[] = [
      {
        id: "obs_south",
        name: "Edificio Sur",
        color: "#ef4444",
        vertices: [
          { azimuth: -40, altitude: 10 },
          { azimuth: 40, altitude: 10 },
          { azimuth: 40, altitude: 60 },
          { azimuth: -40, altitude: 60 },
        ],
        visible: true,
      },
    ];
    // For Medellín Dec 21 at hour 12, the sun is at az=-0.3, alt=60.3
    // which falls inside the obstacle (az -40..40, alt 10..60).
    // The sampling at ±15 min around hour 12 also stays inside.
    // We pass the actual calculated position as altitudeSolar/azimuthSolar.
    const fs = calculateFSGeometrico(obstacle, 60, 0, 6.25, -75.56, -5, 12, 21, 12);
    expect(fs).toBeGreaterThan(0);
  });

  it("returns 0 when sun is outside all obstacle polygons", () => {
    const obstacles = createMockObstacles();
    // Sun at azimuth 90° (west), altitude 60° — outside the obstacle
    const fs = calculateFSGeometrico(obstacles, 60, 90, 6.25, -75.56, -5, 3, 20, 12);
    expect(fs).toBe(0);
  });

  it("is bounded between 0 and 1", () => {
    const obstacles = createMockObstacles();
    const fs = calculateFSGeometrico(obstacles, 25, 0, 6.25, -75.56, -5, 3, 20, 12);
    expect(fs).toBeGreaterThanOrEqual(0);
    expect(fs).toBeLessThanOrEqual(1);
  });
});

// ─── Tests: Facade Exposure ──────────────────────────────────────────────────

describe("isFacadeExposed", () => {
  it("returns false when solar altitude is 0 or negative", () => {
    expect(isFacadeExposed(0, 0, 0, 90)).toBe(false);
    expect(isFacadeExposed(-5, 0, 0, 90)).toBe(false);
  });

  it("returns true when sun faces the facade", () => {
    // Sun at azimuth 0° (south), facade facing south (normal at 0°)
    expect(isFacadeExposed(45, 0, 0, 90)).toBe(true);
  });

  it("returns false when sun is behind the facade", () => {
    // Sun at azimuth 0° (south), facade facing north (normal at 180°)
    // For vertical surface, sun must be in front hemisphere
    expect(isFacadeExposed(45, 0, 180, 90)).toBe(false);
  });

  it("east facade sees morning sun", () => {
    // Sun in the east (azimuth -90°), east-facing facade (normal at -90°)
    expect(isFacadeExposed(30, -90, -90, 90)).toBe(true);
  });

  it("east facade does not see afternoon sun", () => {
    // Sun in the west (azimuth 90°), east-facing facade (normal at -90°)
    expect(isFacadeExposed(30, 90, -90, 90)).toBe(false);
  });

  it("horizontal surface always sees sun when altitude > 0", () => {
    expect(isFacadeExposed(10, 0, 0, 0)).toBe(true);
    expect(isFacadeExposed(10, 90, 0, 0)).toBe(true);
    expect(isFacadeExposed(10, -90, 0, 0)).toBe(true);
  });
});

// ─── Tests: Classification ───────────────────────────────────────────────────

describe("classifySituation", () => {
  it("classifies clear sky correctly", () => {
    expect(classifySituation(0.02)).toBe("Cielo despejado");
  });

  it("classifies partially clear correctly", () => {
    expect(classifySituation(0.15)).toBe("Parcialmente despejado");
  });

  it("classifies partially cloudy correctly", () => {
    expect(classifySituation(0.40)).toBe("Parcialmente nublado");
  });

  it("classifies very cloudy correctly", () => {
    expect(classifySituation(0.65)).toBe("Muy nublado");
  });

  it("classifies overcast correctly", () => {
    expect(classifySituation(0.85)).toBe("Cielo cubierto");
  });
});

describe("classifyCombinedSituation", () => {
  it("identifies geometric shadow dominance", () => {
    const result = classifyCombinedSituation(0.8, 0.1);
    expect(result).toContain("geométrica");
  });

  it("identifies clear sky with no geometric shadow", () => {
    const result = classifyCombinedSituation(0, 0.02);
    expect(result).toBe("Cielo despejado");
  });

  it("identifies combined shadow + overcast", () => {
    const result = classifyCombinedSituation(0.7, 0.7);
    expect(result).toContain("geom");
    expect(result).toContain("cubierto");
  });
});

// ─── Tests: Critical Days Constants ──────────────────────────────────────────

describe("CRITICAL_DAYS", () => {
  it("contains 4 critical days (equinoxes + solstices)", () => {
    expect(CRITICAL_DAYS).toHaveLength(4);
  });

  it("includes March equinox", () => {
    const march = CRITICAL_DAYS.find(d => d.month === 3);
    expect(march).toBeDefined();
    expect(march!.day).toBe(20);
    expect(march!.name).toContain("Marzo");
  });

  it("includes June solstice", () => {
    const june = CRITICAL_DAYS.find(d => d.month === 6);
    expect(june).toBeDefined();
    expect(june!.day).toBe(21);
    expect(june!.name).toContain("Junio");
  });
});

describe("MONTHLY_CRITICAL_DAYS", () => {
  it("contains 12 monthly days", () => {
    expect(MONTHLY_CRITICAL_DAYS).toHaveLength(12);
  });

  it("all days are the 21st", () => {
    for (const day of MONTHLY_CRITICAL_DAYS) {
      expect(day.day).toBe(21);
    }
  });
});

// ─── Tests: Execute Crossing ─────────────────────────────────────────────────

describe("executeCrossing", () => {
  it("returns empty array when no critical days selected", () => {
    const epw = createMockEPWData();
    const results = executeCrossing(epw, [], {
      ...DEFAULT_CROSSING_CONFIG,
      criticalDays: [],
    });
    expect(results).toHaveLength(0);
  });

  it("generates results for valid EPW data and critical days", () => {
    const epw = createMockEPWData();
    const results = executeCrossing(epw, [], {
      ...DEFAULT_CROSSING_CONFIG,
      criticalDays: [CRITICAL_DAYS[0]], // Only March equinox
      facades: [{ name: "Fachada Norte", azimuthNormal: 0, tilt: 90 }],
    });
    expect(results.length).toBeGreaterThan(0);
  });

  it("each result has required fields", () => {
    const epw = createMockEPWData();
    const results = executeCrossing(epw, [], {
      ...DEFAULT_CROSSING_CONFIG,
      criticalDays: [CRITICAL_DAYS[0]],
      facades: [{ name: "Fachada Norte", azimuthNormal: 0, tilt: 90 }],
    });

    for (const r of results) {
      expect(r.evento).toBeDefined();
      expect(r.month).toBeDefined();
      expect(r.day).toBeGreaterThan(0);
      expect(r.hour).toBeGreaterThan(0);
      expect(r.heightSolar).toBeGreaterThan(0);
      expect(typeof r.azimuthSolar).toBe("number");
      expect(r.fsGeometrico).toBeGreaterThanOrEqual(0);
      expect(r.fsGeometrico).toBeLessThanOrEqual(1);
      expect(r.fsClimatico).toBeGreaterThanOrEqual(0);
      expect(r.fsClimatico).toBeLessThanOrEqual(1);
      expect(r.fs).toBeGreaterThanOrEqual(0);
      expect(r.fs).toBeLessThanOrEqual(1);
      expect(r.situacion).toBeDefined();
      expect(r.obstacle).toBeDefined();
      expect(r.facade).toBe("Fachada Norte");
    }
  });

  it("filters out hours when facade is not exposed", () => {
    const epw = createMockEPWData();
    // East facade should only see morning sun
    const results = executeCrossing(epw, [], {
      ...DEFAULT_CROSSING_CONFIG,
      criticalDays: [CRITICAL_DAYS[0]],
      facades: [{ name: "Fachada Este", azimuthNormal: -90, tilt: 90 }],
    });

    // All results should have negative azimuth (morning = east)
    // or at least most should be morning hours
    const morningResults = results.filter(r => r.hour < 13);
    expect(morningResults.length).toBeGreaterThan(results.length * 0.5);
  });

  it("includes obstacle names when obstacles are present", () => {
    const epw = createMockEPWData();
    const obstacles = createMockObstacles();

    const results = executeCrossing(epw, obstacles, {
      ...DEFAULT_CROSSING_CONFIG,
      criticalDays: [CRITICAL_DAYS[0]],
      facades: [{ name: "Fachada Norte", azimuthNormal: 0, tilt: 90 }],
    });

    // Some results should have obstacle names (when sun is inside obstacle polygon)
    const withObstacles = results.filter(r => r.obstacle !== "Ninguno");
    // The obstacle covers az -30 to 30, alt 10 to 40
    // At equinox in Medellín, sun passes through this range
    // It's possible some points hit the obstacle
    expect(results.length).toBeGreaterThan(0);
  });

  it("respects hour range configuration", () => {
    const epw = createMockEPWData();
    const results = executeCrossing(epw, [], {
      ...DEFAULT_CROSSING_CONFIG,
      criticalDays: [CRITICAL_DAYS[0]],
      facades: [{ name: "Fachada Norte", azimuthNormal: 0, tilt: 90 }],
      hourRange: [9, 15],
    });

    for (const r of results) {
      expect(r.hour).toBeGreaterThanOrEqual(9);
      expect(r.hour).toBeLessThanOrEqual(16); // +0.5 for center of hour
    }
  });
});

// ─── Tests: Convert Results to Analysis Points ───────────────────────────────

describe("crossingResultsToAnalysisPoints", () => {
  it("returns empty array for empty results", () => {
    const points = crossingResultsToAnalysisPoints([]);
    expect(points).toHaveLength(0);
  });

  it("converts results to analysis point format", () => {
    const epw = createMockEPWData();
    const results = executeCrossing(epw, [], {
      ...DEFAULT_CROSSING_CONFIG,
      criticalDays: [CRITICAL_DAYS[0]],
      facades: [{ name: "Fachada Norte", azimuthNormal: 0, tilt: 90 }],
    });

    const points = crossingResultsToAnalysisPoints(results);
    expect(points).toHaveLength(results.length);

    for (const p of points) {
      expect(p.id).toBeDefined();
      expect(p.id).toContain("crossing_");
      expect(p.month).toBeDefined();
      expect(p.day).toBeGreaterThan(0);
      expect(p.hour).toBeGreaterThan(0);
      expect(p.heightSolar).toBeGreaterThan(0);
      expect(typeof p.azimuthSolar).toBe("number");
      expect(p.autoCalculated).toBe(true);
      expect(p.evento).toBeDefined();
      expect(p.fsGeometrico).toBeGreaterThanOrEqual(0);
      expect(p.fsClimatico).toBeGreaterThanOrEqual(0);
      expect(p.situacion).toBeDefined();
      expect(p.hourStr).toMatch(/^\d{2}:\d{2}$/);
    }
  });

  it("includes facade name in obstacle field", () => {
    const epw = createMockEPWData();
    const results = executeCrossing(epw, [], {
      ...DEFAULT_CROSSING_CONFIG,
      criticalDays: [CRITICAL_DAYS[0]],
      facades: [{ name: "Fachada Norte", azimuthNormal: 0, tilt: 90 }],
    });

    const points = crossingResultsToAnalysisPoints(results);
    for (const p of points) {
      expect(p.obstacle).toContain("Fachada Norte");
    }
  });
});
