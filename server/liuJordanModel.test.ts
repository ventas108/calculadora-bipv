import { describe, expect, it } from "vitest";
import {
  calculateSolarAngles,
  calculateIncidenceAngle,
  calculatePOARadiation,
  calculatePOARadiationPerez,
  calculateHourlyPOA,
} from "../client/src/lib/liuJordanModel";

describe("liuJordanModel", () => {
  describe("calculateSolarAngles", () => {
    it("returns a zenith angle within [0, pi] and airmass=1 at zenith 0", () => {
      // Ecuador, meridiano estándar == longitud (sin corrección horaria),
      // día del equinoccio (~81), mediodía solar exacto.
      const angles = calculateSolarAngles(0, -75, -75, 81, 12, 0);
      expect(angles.zenithAngle).toBeGreaterThanOrEqual(0);
      expect(angles.zenithAngle).toBeLessThanOrEqual(Math.PI);
      // Cerca del mediodía solar en el equinoccio y el ecuador, el sol está
      // casi en el cenit (ángulo cenital pequeño).
      expect(angles.zenithAngle).toBeLessThan(0.1);
      expect(angles.airmass).toBeCloseTo(1 / Math.cos(angles.zenithAngle), 6);
    });

    it("uses airmass=999 sentinel when the sun is below the horizon", () => {
      // Medianoche solar: el sol está muy por debajo del horizonte.
      const angles = calculateSolarAngles(4.6, -74.1, -75, 172, 0, 0);
      expect(angles.zenithAngle).toBeGreaterThan(Math.PI / 2);
      expect(angles.airmass).toBe(999);
    });
  });

  describe("calculateIncidenceAngle", () => {
    it("equals the zenith angle for a horizontal surface (tilt=0)", () => {
      const zenith = 0.4;
      const azimuthSun = 0.2;
      const incidence = calculateIncidenceAngle(zenith, azimuthSun, 0, 0);
      expect(incidence).toBeCloseTo(zenith, 10);
    });

    it("is capped at pi/2 (never reports incidence beyond the horizon)", () => {
      // Sol detrás de la superficie: zenith pequeño pero azimut opuesto al
      // panel y panel muy inclinado -- coseno del ángulo de incidencia < 0.
      const incidence = calculateIncidenceAngle(0.1, Math.PI, Math.PI / 2, 0);
      expect(incidence).toBeLessThanOrEqual(Math.PI / 2);
    });
  });

  describe("calculatePOARadiation (Liu-Jordan) -- irradiancia nula", () => {
    it("returns all-zero POA when DNI, DHI and GHI are all zero", () => {
      const solarAngles = calculateSolarAngles(4.6, -74.1, -75, 172, 12, 0);
      const poa = calculatePOARadiation(0, 0, 0, solarAngles, 0.3, 0, 0.2, 4.6);
      expect(poa.totalPOA).toBe(0);
      expect(poa.directPOA).toBe(0);
      expect(poa.diffusePOA).toBe(0);
      expect(poa.reflectedPOA).toBe(0);
    });
  });

  describe("calculatePOARadiation (Liu-Jordan) -- invariantes en superficie horizontal", () => {
    // Con tilt=0 (superficie horizontal): incidence=zenith, diffusePOA=DHI
    // completo (ve toda la bóveda celeste) y reflectedPOA=0 (no ve el suelo).
    const zenith = 0.5;
    const solarAngles = { zenithAngle: zenith, azimuthAngle: 0, incidenceAngle: 0, airmass: 1 / Math.cos(zenith) };

    it("diffusePOA equals DHI on a horizontal surface", () => {
      const poa = calculatePOARadiation(500, 150, 700, solarAngles, 0, 0, 0.2, 4.6);
      expect(poa.diffusePOA).toBeCloseTo(150, 6);
    });

    it("reflectedPOA is zero on a horizontal surface", () => {
      const poa = calculatePOARadiation(500, 150, 700, solarAngles, 0, 0, 0.2, 4.6);
      expect(poa.reflectedPOA).toBeCloseTo(0, 6);
    });

    it("directPOA equals DNI*cos(zenith) on a horizontal surface", () => {
      const poa = calculatePOARadiation(500, 150, 700, solarAngles, 0, 0, 0.2, 4.6);
      expect(poa.directPOA).toBeCloseTo(500 * Math.cos(zenith), 6);
    });

    it("totalPOA is never negative even with a sun behind the panel", () => {
      // Panel vertical, azimut solar opuesto al panel: cos(incidencia) < 0
      // para la componente directa -- debe recortarse a 0, no restar.
      const behindAngles = { zenithAngle: 0.3, azimuthAngle: Math.PI, incidenceAngle: 0, airmass: 1 };
      const poa = calculatePOARadiation(800, 100, 400, behindAngles, Math.PI / 2, 0, 0.2, 4.6);
      expect(poa.directPOA).toBeCloseTo(0, 9);
      expect(poa.totalPOA).toBeGreaterThanOrEqual(0);
    });
  });

  describe("calculatePOARadiationPerez -- irradiancia nula (guarda kd=0 cuando GHI<=0)", () => {
    it("una hora completamente nula (DNI=DHI=GHI=0) devuelve componentes finitas y totalPOA=0", () => {
      // Antes de este fix, GHI=0 hacía kd = DHI/GHI = 0/0 = NaN, contaminando
      // f1/f2 y por tanto diffusePOA/totalPOA. Con la guarda (kd=0 si GHI<=0),
      // todas las componentes son 0 y finitas, igual que Liu-Jordan.
      const solarAngles = calculateSolarAngles(4.6, -74.1, -75, 172, 12, 0);
      const poa = calculatePOARadiationPerez(0, 0, 0, solarAngles, 0.3, 0, 0.2, 4.6);
      expect(Number.isFinite(poa.totalPOA)).toBe(true);
      expect(Number.isFinite(poa.directPOA)).toBe(true);
      expect(Number.isFinite(poa.diffusePOA)).toBe(true);
      expect(Number.isFinite(poa.reflectedPOA)).toBe(true);
      expect(poa.totalPOA).toBe(0);
      expect(poa.directPOA).toBe(0);
      expect(poa.diffusePOA).toBe(0);
      expect(poa.reflectedPOA).toBe(0);
    });

    it("GHI=0 con DNI>0 (dato de calidad dudosa pero posible) no produce NaN", () => {
      // Físicamente inconsistente (GHI≈DNI·cosZ+DHI implicaría GHI>0 si DNI>0
      // y el sol está sobre el horizonte), pero el contrato de tipos de
      // calculateHourlyPOA lo permite -- una fila de EPW con datos corruptos
      // no debe romper el cálculo del resto del mes.
      const solarAngles = calculateSolarAngles(4.6, -74.1, -75, 172, 12, 0);
      const poa = calculatePOARadiationPerez(500, 0, 0, solarAngles, 0.3, 0, 0.2, 4.6);
      expect(Number.isFinite(poa.totalPOA)).toBe(true);
      expect(Number.isFinite(poa.diffusePOA)).toBe(true);
      expect(poa.diffusePOA).toBe(0); // DHI=0 -> sin componente difusa, sin NaN
      // La componente directa sigue siendo válida (depende solo de DNI y el ángulo de incidencia).
      expect(poa.directPOA).toBeGreaterThan(0);
      expect(poa.totalPOA).toBeCloseTo(poa.directPOA, 6);
    });

    it("GHI>0 sigue calculando kd normalmente (no altera el comportamiento con entradas válidas)", () => {
      const solarAngles = calculateSolarAngles(4.6, -74.1, -75, 172, 12, 0);
      const poaConGHI = calculatePOARadiationPerez(500, 150, 700, solarAngles, 0.3, 0, 0.2, 4.6);
      expect(Number.isFinite(poaConGHI.totalPOA)).toBe(true);
      expect(poaConGHI.totalPOA).toBeGreaterThan(0);
    });
  });

  describe("calculateHourlyPOA", () => {
    it("selects Liu-Jordan by default (usePerezModel=false)", () => {
      const poa = calculateHourlyPOA(4.6, -74.1, -75, 172, 12, 0, 500, 150, 700, 0.3, 0, 0.2, false);
      expect(poa.components.diffuseCircumSolar).toBe(0);
      expect(poa.components.diffuseHorizonBand).toBe(0);
    });

    it("selects Perez when usePerezModel=true", () => {
      const poa = calculateHourlyPOA(4.6, -74.1, -75, 172, 12, 0, 500, 150, 700, 0.3, 0, 0.2, true);
      // Con irradiancia real (no nula) el modelo Perez sí es finito.
      expect(Number.isFinite(poa.totalPOA)).toBe(true);
    });

    it("returns zero POA for a fully null-irradiance hour with Liu-Jordan", () => {
      const poa = calculateHourlyPOA(4.6, -74.1, -75, 172, 0, 0, 0, 0, 0, 0.3, 0, 0.2, false);
      expect(poa.totalPOA).toBe(0);
    });
  });
});
