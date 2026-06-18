/**
 * Modelo Isotrópico Liu-Jordan para cálculo de radiación POA
 * Estándar para sistemas BIPV (Building Integrated Photovoltaics)
 * 
 * Referencias:
 * - Liu, B. Y. H., & Jordan, R. C. (1961). The interrelationship and characteristic
 *   distribution of direct, diffuse and total solar radiation. Solar Energy, 4(3), 1-19.
 * - Perez, R., Stewart, R., Arbogast, C., Seals, R., & Scott, J. (1986). An anisotropic
 *   hourly diffuse radiation model for sloped surfaces: Description, performance validation,
 *   and applications. Solar Energy, 36(6), 481-497.
 */

export interface SolarAngles {
  zenithAngle: number; // Ángulo cenital (radianes)
  azimuthAngle: number; // Ángulo azimutal solar (radianes)
  incidenceAngle: number; // Ángulo de incidencia en la superficie (radianes)
  airmass: number; // Masa de aire
}

export interface POARadiation {
  directPOA: number; // Radiación directa en POA (W/m²)
  diffusePOA: number; // Radiación difusa en POA (W/m²)
  reflectedPOA: number; // Radiación reflejada en POA (W/m²)
  totalPOA: number; // Radiación total en POA (W/m²)
  components: {
    directBeam: number;
    diffuseIsotropic: number;
    diffuseCircumSolar: number;
    diffuseHorizonBand: number;
    reflected: number;
  };
}

/**
 * Calcula los ángulos solares para una ubicación y hora específica
 */
export const calculateSolarAngles = (
  latitude: number, // grados
  longitude: number, // grados
  standardMeridian: number, // grados (zona horaria)
  dayOfYear: number, // 1-365
  hourOfDay: number, // 0-23
  minute: number = 0 // 0-59
): SolarAngles => {
  const lat = (latitude * Math.PI) / 180;
  const lon = (longitude * Math.PI) / 180;
  const stdMer = (standardMeridian * Math.PI) / 180;

  // Ecuación del tiempo (minutos)
  const B = ((dayOfYear - 1) * 360) / 365;
  const B_rad = (B * Math.PI) / 180;
  const E = 229.2 * (0.000075 + 0.001868 * Math.cos(B_rad) - 0.032077 * Math.sin(B_rad) - 0.014615 * Math.cos(2 * B_rad) - 0.040849 * Math.sin(2 * B_rad));

  // Hora solar local (minutos desde medianoche)
  const timeOffset = (lon - stdMer) * 180 / Math.PI * 4; // Conversión a minutos
  const solarTime = hourOfDay * 60 + minute + E + timeOffset / 60;
  const solarHour = solarTime / 60;

  // Ángulo horario (radianes)
  const hourAngle = ((solarHour - 12) * 15 * Math.PI) / 180;

  // Declinación solar (radianes)
  const declination = (23.45 * Math.sin(B_rad - (80 * Math.PI) / 180) * Math.PI) / 180;

  // Ángulo cenital (radianes)
  const zenithAngle = Math.acos(
    Math.sin(lat) * Math.sin(declination) + Math.cos(lat) * Math.cos(declination) * Math.cos(hourAngle)
  );

  // Ángulo azimutal solar (radianes, 0=Sur, π/2=Oeste, -π/2=Este)
  const azimuthAngle = Math.atan2(
    Math.sin(hourAngle),
    Math.cos(lat) * Math.tan(declination) - Math.sin(lat) * Math.cos(hourAngle)
  );

  // Masa de aire
  const airmass = zenithAngle < Math.PI / 2 ? 1 / Math.cos(zenithAngle) : 999;

  return {
    zenithAngle,
    azimuthAngle,
    incidenceAngle: 0, // Se calcula después
    airmass,
  };
};

/**
 * Calcula el ángulo de incidencia en una superficie inclinada
 */
export const calculateIncidenceAngle = (
  zenithAngle: number,
  azimuthAngle: number,
  tiltAngle: number, // radianes
  surfaceAzimuth: number // radianes
): number => {
  const incidenceAngle = Math.acos(
    Math.cos(zenithAngle) * Math.cos(tiltAngle) +
    Math.sin(zenithAngle) * Math.sin(tiltAngle) * Math.cos(azimuthAngle - surfaceAzimuth)
  );

  return Math.min(incidenceAngle, Math.PI / 2); // Máximo 90°
};

/**
 * Modelo Liu-Jordan isotrópico para radiación POA
 * Implementa el modelo estándar de la industria BIPV
 */
export const calculatePOARadiation = (
  directNormalIrradiance: number, // DNI (W/m²)
  diffuseHorizontalIrradiance: number, // DHI (W/m²)
  globalHorizontalIrradiance: number, // GHI (W/m²)
  solarAngles: SolarAngles,
  tiltAngle: number, // radianes
  surfaceAzimuth: number, // radianes
  albedo: number = 0.2, // Reflectancia del suelo
  latitude: number // grados, para cálculo de masa de aire
): POARadiation => {
  // Calcular ángulo de incidencia
  const incidenceAngle = calculateIncidenceAngle(
    solarAngles.zenithAngle,
    solarAngles.azimuthAngle,
    tiltAngle,
    surfaceAzimuth
  );

  // 1. COMPONENTE DIRECTA (Direct Beam)
  const directBeam = directNormalIrradiance * Math.max(0, Math.cos(incidenceAngle));

  // 2. COMPONENTE DIFUSA (Modelo Liu-Jordan Isotrópico)
  // La radiación difusa se asume uniformemente distribuida en la bóveda celeste
  const diffuseIsotropic = diffuseHorizontalIrradiance * (1 + Math.cos(tiltAngle)) / 2;

  // 3. COMPONENTE REFLEJADA (Reflected)
  // Radiación reflejada desde el suelo hacia la superficie
  const groundReflectedRadiance = globalHorizontalIrradiance * albedo * (1 - Math.cos(tiltAngle)) / 2;

  // 4. RADIACIÓN TOTAL POA
  const totalPOA = directBeam + diffuseIsotropic + groundReflectedRadiance;

  return {
    directPOA: directBeam,
    diffusePOA: diffuseIsotropic,
    reflectedPOA: groundReflectedRadiance,
    totalPOA: Math.max(0, totalPOA),
    components: {
      directBeam,
      diffuseIsotropic,
      diffuseCircumSolar: 0, // No incluido en modelo básico Liu-Jordan
      diffuseHorizonBand: 0, // No incluido en modelo básico Liu-Jordan
      reflected: groundReflectedRadiance,
    },
  };
};

/**
 * Modelo mejorado Perez (más preciso que Liu-Jordan)
 * Incluye componentes circunsolar y de horizonte
 */
export const calculatePOARadiationPerez = (
  directNormalIrradiance: number,
  diffuseHorizontalIrradiance: number,
  globalHorizontalIrradiance: number,
  solarAngles: SolarAngles,
  tiltAngle: number,
  surfaceAzimuth: number,
  albedo: number = 0.2,
  latitude: number
): POARadiation => {
  const incidenceAngle = calculateIncidenceAngle(
    solarAngles.zenithAngle,
    solarAngles.azimuthAngle,
    tiltAngle,
    surfaceAzimuth
  );

  // Componente directa
  const directBeam = directNormalIrradiance * Math.max(0, Math.cos(incidenceAngle));

  // Índice de claridad
  const kt = globalHorizontalIrradiance / (solarAngles.airmass * 1367 * Math.cos(solarAngles.zenithAngle));
  const kd = diffuseHorizontalIrradiance / globalHorizontalIrradiance;

  // Coeficientes Perez
  let f1 = 0, f2 = 0;
  if (kd <= 0.3) {
    f1 = 1.020 - 0.254 * kd + 0.0123 * Math.sin(solarAngles.zenithAngle);
    f2 = 0.506 - 0.025 * kd - 0.0407 * Math.sin(solarAngles.zenithAngle);
  } else if (kd <= 0.78) {
    f1 = 1.400 - 1.749 * kd + 0.177 * Math.sin(solarAngles.zenithAngle);
    f2 = 0.507 - 0.205 * kd - 0.080 * Math.sin(solarAngles.zenithAngle);
  } else {
    f1 = 0.375 - 0.513 * kd + 0.205 * Math.sin(solarAngles.zenithAngle);
    f2 = 0.107 + 0.027 * kd - 0.078 * Math.sin(solarAngles.zenithAngle);
  }

  // Componente difusa isotrópica
  const diffuseIsotropic = diffuseHorizontalIrradiance * (1 + Math.cos(tiltAngle)) / 2;

  // Componente circunsolar (alrededor del disco solar)
  const diffuseCircumSolar = diffuseHorizontalIrradiance * f1 * Math.max(0, Math.cos(incidenceAngle));

  // Componente de horizonte (cerca del horizonte)
  const diffuseHorizonBand = diffuseHorizontalIrradiance * f2 * Math.sin(tiltAngle);

  // Componente reflejada
  const reflected = globalHorizontalIrradiance * albedo * (1 - Math.cos(tiltAngle)) / 2;

  const totalPOA = directBeam + diffuseIsotropic + diffuseCircumSolar + diffuseHorizonBand + reflected;

  return {
    directPOA: directBeam,
    diffusePOA: diffuseIsotropic + diffuseCircumSolar + diffuseHorizonBand,
    reflectedPOA: reflected,
    totalPOA: Math.max(0, totalPOA),
    components: {
      directBeam,
      diffuseIsotropic,
      diffuseCircumSolar,
      diffuseHorizonBand,
      reflected,
    },
  };
};

/**
 * Calcula radiación POA para un punto horario completo
 */
export const calculateHourlyPOA = (
  latitude: number,
  longitude: number,
  standardMeridian: number,
  dayOfYear: number,
  hourOfDay: number,
  minute: number,
  directNormalIrradiance: number,
  diffuseHorizontalIrradiance: number,
  globalHorizontalIrradiance: number,
  tiltAngle: number,
  surfaceAzimuth: number,
  albedo: number = 0.2,
  usePerezModel: boolean = false
): POARadiation => {
  // Calcular ángulos solares
  const solarAngles = calculateSolarAngles(
    latitude,
    longitude,
    standardMeridian,
    dayOfYear,
    hourOfDay,
    minute
  );

  // Agregar ángulo de incidencia a los ángulos solares
  solarAngles.incidenceAngle = calculateIncidenceAngle(
    solarAngles.zenithAngle,
    solarAngles.azimuthAngle,
    tiltAngle,
    surfaceAzimuth
  );

  // Usar modelo Perez si está disponible, si no usar Liu-Jordan
  if (usePerezModel) {
    return calculatePOARadiationPerez(
      directNormalIrradiance,
      diffuseHorizontalIrradiance,
      globalHorizontalIrradiance,
      solarAngles,
      tiltAngle,
      surfaceAzimuth,
      albedo,
      latitude
    );
  } else {
    return calculatePOARadiation(
      directNormalIrradiance,
      diffuseHorizontalIrradiance,
      globalHorizontalIrradiance,
      solarAngles,
      tiltAngle,
      surfaceAzimuth,
      albedo,
      latitude
    );
  }
};
