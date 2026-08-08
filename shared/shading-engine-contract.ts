/**
 * Contrato neutral entre la interfaz React y el motor solar Python.
 *
 * React puede consumir estos tipos, pero no calcula ni sustituye los resultados
 * oficiales. El motor Python es la autoridad de FS_geometrico.
 */

export const SHADING_ENGINE_CONTRACT_VERSION = "bipv.shading.v1" as const;

export interface ShadingEngineLocation {
  latitude: number;
  longitude: number;
  timezone: number;
  elevation_m: number;
}

export interface ShadingEnginePoint {
  id: string;
  facade: string;
  x_m: number;
  y_m: number;
  z_m: number;
}

export interface ShadingEngineTriangle {
  a: [number, number, number];
  b: [number, number, number];
  c: [number, number, number];
}

export interface ShadingEngineRequest {
  contract_version: typeof SHADING_ENGINE_CONTRACT_VERSION;
  timestamps_utc: string[];
  location: ShadingEngineLocation;
  points: ShadingEnginePoint[];
  triangles: ShadingEngineTriangle[];
  transparency?: number;
}

export interface ShadingEngineResultRow {
  timestamp_utc: string;
  month: number;
  day: number;
  hour_utc: number;
  solar_altitude_deg: number;
  solar_azimuth_deg: number;
  point_id: string;
  facade: string;
  fs_geometrico: number;
  /** Null by design: cloud losses never activate mismatch/bypass. */
  fs_climatico: null;
  /** Null by design: production composes this only inside BIPV. */
  fs_combinado: null;
  /** The only factor consumed by mismatch/bypass. */
  fs: number;
}

export interface ShadingEngineResult {
  contract_version: typeof SHADING_ENGINE_CONTRACT_VERSION;
  engine: "python";
  authority: "official_solar_engine";
  conventions: {
    timestamp: "UTC";
    azimuth: "north_clockwise";
    coordinates: "x_east_y_north_z_up_m";
    fs_geometrico: "0_no_geometric_shadow_1_total_geometric_shadow";
  };
  results: ShadingEngineResultRow[];
}

function finite(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

/**
 * Valida solamente la frontera de resultados. La física sigue siendo Python;
 * esta función evita que la UI consuma un payload ambiguo o financiero.
 */
export function isOfficialShadingEngineResult(
  value: unknown,
): value is ShadingEngineResult {
  if (!value || typeof value !== "object") return false;
  const payload = value as Partial<ShadingEngineResult>;
  if (
    payload.contract_version !== SHADING_ENGINE_CONTRACT_VERSION ||
    payload.engine !== "python" ||
    payload.authority !== "official_solar_engine" ||
    !Array.isArray(payload.results)
  ) {
    return false;
  }

  return payload.results.every((row) => {
    if (!row || typeof row !== "object") return false;
    const item = row as Partial<ShadingEngineResultRow>;
    const month = item.month;
    const day = item.day;
    const hourUtc = item.hour_utc;
    return (
      typeof item.timestamp_utc === "string" &&
      typeof month === "number" &&
      Number.isInteger(month) &&
      month >= 1 &&
      month <= 12 &&
      typeof day === "number" &&
      Number.isInteger(day) &&
      day >= 1 &&
      day <= 31 &&
      typeof hourUtc === "number" &&
      Number.isInteger(hourUtc) &&
      hourUtc >= 0 &&
      hourUtc <= 23 &&
      finite(item.solar_altitude_deg) &&
      finite(item.solar_azimuth_deg) &&
      typeof item.point_id === "string" &&
      typeof item.facade === "string" &&
      finite(item.fs_geometrico) &&
      item.fs_geometrico >= 0 &&
      item.fs_geometrico <= 1 &&
      item.fs_climatico === null &&
      item.fs_combinado === null &&
      finite(item.fs) &&
      Math.abs(item.fs - item.fs_geometrico) <= 1e-9
    );
  });
}