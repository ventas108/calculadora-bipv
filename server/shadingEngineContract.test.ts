import { describe, expect, it } from "vitest";
import reference from "../docs/fixtures/sombreado-referencia.json";
import {
  calculateSolarPosition,
} from "@/lib/solarPosition";
import {
  isOfficialShadingEngineResult,
  SHADING_ENGINE_CONTRACT_VERSION,
} from "@shared/shading-engine-contract";

describe("contrato oficial del motor de sombreado", () => {
  it("mantiene la posición solar TS dentro de la tolerancia de referencia pvlib", () => {
    for (const testCase of reference.solar_position_cases) {
      const instant = new Date(testCase.timestamp_utc);
      const month = instant.getUTCMonth() + 1;
      const day = instant.getUTCDate();
      const hourUtc = instant.getUTCHours() + instant.getUTCMinutes() / 60;
      const hourLocal = hourUtc + reference.location.timezone;
      const position = calculateSolarPosition(
        reference.location.latitude,
        reference.location.longitude,
        reference.location.timezone,
        month,
        day,
        hourLocal,
      );

      expect(Math.abs(position.altitude - testCase.expected_altitude_deg)).toBeLessThan(
        testCase.tolerance_deg,
      );
      // TS: 0°=Sur, negativo=Este, positivo=Oeste.
      // pvlib: 0°=Norte, sentido horario. Por tanto: pvlib = 180° + TS.
      const pvlibAzimuth = (180 + position.azimuth + 360) % 360;
      expect(Math.abs(pvlibAzimuth - testCase.expected_azimuth_deg)).toBeLessThan(
        testCase.tolerance_deg,
      );
    }
  });

  it("rechaza resultados que mezclen clima o finanzas con FS_geometrico", () => {
    const valid = {
      contractVersion: SHADING_ENGINE_CONTRACT_VERSION,
      engine: "python" as const,
      authority: "official_solar_engine" as const,
      conventions: {
        timestamp: "UTC" as const,
        azimuth: "north_clockwise" as const,
        coordinates: "x_east_y_north_z_up_m" as const,
        fsGeometrico: "0_no_geometric_shadow_1_total_geometric_shadow" as const,
      },
      results: [{
        timestamp_utc: "2024-03-20T17:00:00Z",
        month: 3,
        day: 20,
        hour_utc: 17,
        solar_altitude_deg: 83.5,
        solar_azimuth_deg: 158.4,
        point_id: "P1",
        facade: "Sur",
        fs_geometrico: 1,
        fs_climatico: null,
        fs_combinado: null,
        fs: 1,
      }],
    };
    expect(isOfficialShadingEngineResult(valid)).toBe(true);
    expect(isOfficialShadingEngineResult({
      ...valid,
      results: [{ ...valid.results[0], fs_climatico: 0.4 }],
    })).toBe(false);
    expect(isOfficialShadingEngineResult({
      ...valid,
      results: [{ ...valid.results[0], fs: 0.4 }],
    })).toBe(false);
  });
});