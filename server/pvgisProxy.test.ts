import { describe, expect, it } from "vitest";
import {
  estimateAnnualIrradiance,
  classifyIrradiance,
  generateIrradianceGrid,
  calculateRegionStats,
} from "../client/src/lib/irradianceHeatmap";

describe("irradianceHeatmap library", () => {
  describe("estimateAnnualIrradiance", () => {
    it("returns higher irradiance near the equator", () => {
      const equator = estimateAnnualIrradiance(0, -75);
      const highLat = estimateAnnualIrradiance(60, -75);
      expect(equator).toBeGreaterThan(highLat);
    });

    it("returns value within valid range (800-2200)", () => {
      const irradiance = estimateAnnualIrradiance(6.25, -75.56); // Medellín
      expect(irradiance).toBeGreaterThanOrEqual(800);
      expect(irradiance).toBeLessThanOrEqual(2200);
    });

    it("returns reasonable value for Medellín (tropical)", () => {
      const irradiance = estimateAnnualIrradiance(6.25, -75.56);
      // Medellín should have good irradiance (1400-1900 range)
      expect(irradiance).toBeGreaterThan(1400);
      expect(irradiance).toBeLessThan(1900);
    });

    it("returns reasonable value for high latitude", () => {
      const irradiance = estimateAnnualIrradiance(65, 25); // Northern Finland
      expect(irradiance).toBeLessThan(1400);
    });
  });

  describe("classifyIrradiance", () => {
    it("classifies excellent irradiance correctly", () => {
      const result = classifyIrradiance(2100);
      expect(result.category).toBe("Excelente");
      expect(result.color).toBe("#d32f2f");
    });

    it("classifies very good irradiance correctly", () => {
      const result = classifyIrradiance(1900);
      expect(result.category).toBe("Muy Buena");
      expect(result.color).toBe("#f57c00");
    });

    it("classifies good irradiance correctly", () => {
      const result = classifyIrradiance(1700);
      expect(result.category).toBe("Buena");
      expect(result.color).toBe("#fbc02d");
    });

    it("classifies acceptable irradiance correctly", () => {
      const result = classifyIrradiance(1500);
      expect(result.category).toBe("Aceptable");
      expect(result.color).toBe("#7cb342");
    });

    it("classifies limited irradiance correctly", () => {
      const result = classifyIrradiance(1300);
      expect(result.category).toBe("Limitada");
      expect(result.color).toBe("#1976d2");
    });

    it("classifies very limited irradiance correctly", () => {
      const result = classifyIrradiance(1000);
      expect(result.category).toBe("Muy Limitada");
      expect(result.color).toBe("#424242");
    });
  });

  describe("generateIrradianceGrid", () => {
    it("generates correct number of points", () => {
      const points = generateIrradianceGrid(6.25, -75.56, 200);
      // 15x15 grid = 225 points (some may be filtered by bounds)
      expect(points.length).toBeGreaterThan(0);
      expect(points.length).toBeLessThanOrEqual(225);
    });

    it("all points have valid irradiance values", () => {
      const points = generateIrradianceGrid(6.25, -75.56, 100);
      points.forEach(point => {
        expect(point.irradiance).toBeGreaterThanOrEqual(800);
        expect(point.irradiance).toBeLessThanOrEqual(2200);
        expect(point.weight).toBeGreaterThanOrEqual(0);
        expect(point.weight).toBeLessThanOrEqual(1);
      });
    });

    it("points are within the specified radius", () => {
      const centerLat = 6.25;
      const centerLng = -75.56;
      const radiusKm = 200;
      const radiusDeg = radiusKm / 111;
      const points = generateIrradianceGrid(centerLat, centerLng, radiusKm);

      points.forEach(point => {
        expect(point.lat).toBeGreaterThanOrEqual(centerLat - radiusDeg - 0.1);
        expect(point.lat).toBeLessThanOrEqual(centerLat + radiusDeg + 0.1);
      });
    });
  });

  describe("calculateRegionStats", () => {
    it("calculates correct stats for sample data", () => {
      const points = [
        { lat: 0, lng: 0, irradiance: 1000, weight: 0.2 },
        { lat: 0, lng: 0, irradiance: 1500, weight: 0.5 },
        { lat: 0, lng: 0, irradiance: 2000, weight: 0.8 },
      ];
      const stats = calculateRegionStats(points);
      expect(stats.min).toBe(1000);
      expect(stats.max).toBe(2000);
      expect(stats.average).toBeCloseTo(1500, 0);
      expect(stats.median).toBe(1500);
      expect(stats.stdDev).toBeGreaterThan(0);
    });

    it("handles empty array", () => {
      const stats = calculateRegionStats([]);
      expect(stats.average).toBe(0);
      expect(stats.min).toBe(0);
      expect(stats.max).toBe(0);
    });
  });
});
