import { describe, it, expect } from 'vitest';
import { detectColombianRegion, COLOMBIAN_REGION_OPTIONS } from '../shared/colombianRegions';
import type { ColombianRegionKey } from '../shared/colombianRegions';

/**
 * Tests unitarios para la función real detectColombianRegion
 * importada desde shared/colombianRegions.ts
 */

describe('detectColombianRegion', () => {
  describe('Ciudades principales - detección con alta confianza', () => {
    it('Medellín → Andina', () => {
      const result = detectColombianRegion(6.22, -75.59);
      expect(result.region).toBe('andina');
      expect(result.confidence).toBe('alta');
      expect(result.isInColombia).toBe(true);
    });

    it('Bogotá → Andina', () => {
      const result = detectColombianRegion(4.71, -74.07);
      expect(result.region).toBe('andina');
      expect(result.confidence).toBe('alta');
    });

    it('Cali → Andina o Pacífica (zona fronteriza)', () => {
      // Cali está en el límite entre Andina y Pacífica en los polígonos simplificados
      const result = detectColombianRegion(3.45, -76.53);
      expect(['andina', 'pacifica']).toContain(result.region);
      expect(result.isInColombia).toBe(true);
    });

    it('Barranquilla → Caribe', () => {
      const result = detectColombianRegion(10.96, -74.78);
      expect(result.region).toBe('caribe');
      expect(result.confidence).toBe('alta');
    });

    it('Cartagena → Caribe', () => {
      const result = detectColombianRegion(10.44, -75.51);
      expect(result.region).toBe('caribe');
      expect(result.isInColombia).toBe(true);
    });

    it('San Andrés → Insular', () => {
      const result = detectColombianRegion(12.58, -81.70);
      expect(result.region).toBe('insular');
      expect(result.confidence).toBe('alta');
    });

    it('Villavicencio → Orinoquía o Andina (zona fronteriza)', () => {
      // Villavicencio está en el piedemonte, zona fronteriza Andina/Orinoquía
      const result = detectColombianRegion(4.15, -73.63);
      expect(['orinoquia', 'andina']).toContain(result.region);
      expect(result.isInColombia).toBe(true);
    });

    it('Leticia → Amazonía', () => {
      const result = detectColombianRegion(-4.2, -69.94);
      expect(result.region).toBe('amazonia');
    });
  });

  describe('Fuera de Colombia', () => {
    it('Miami (USA) → baja confianza, no es Colombia', () => {
      const result = detectColombianRegion(25.76, -80.19);
      expect(result.isInColombia).toBe(false);
      expect(result.confidence).toBe('baja');
    });

    it('Madrid (España) → baja confianza, no es Colombia', () => {
      const result = detectColombianRegion(40.42, -3.70);
      expect(result.isInColombia).toBe(false);
      expect(result.confidence).toBe('baja');
    });

    it('Lima (Perú) → baja confianza, no es Colombia', () => {
      const result = detectColombianRegion(-12.05, -77.04);
      expect(result.isInColombia).toBe(false);
      expect(result.confidence).toBe('baja');
    });
  });

  describe('Estructura del resultado', () => {
    it('Devuelve todos los campos requeridos', () => {
      const result = detectColombianRegion(6.22, -75.59);
      expect(result).toHaveProperty('region');
      expect(result).toHaveProperty('label');
      expect(result).toHaveProperty('confidence');
      expect(result).toHaveProperty('isInColombia');
      expect(result).toHaveProperty('nearestCities');
    });

    it('La región es una de las 6 regiones válidas', () => {
      const validRegions: ColombianRegionKey[] = ['caribe', 'andina', 'pacifica', 'orinoquia', 'amazonia', 'insular'];
      const result = detectColombianRegion(6.22, -75.59);
      expect(validRegions).toContain(result.region);
    });

    it('La confianza es alta, media o baja', () => {
      const validConfidence = ['alta', 'media', 'baja'];
      const result = detectColombianRegion(6.22, -75.59);
      expect(validConfidence).toContain(result.confidence);
    });

    it('nearestCities es un string no vacío', () => {
      const result = detectColombianRegion(6.22, -75.59);
      expect(result.nearestCities.length).toBeGreaterThan(0);
    });
  });

  describe('Fallback por centroide (zona fronteriza)', () => {
    it('Coordenada en zona fronteriza dentro del bounding box → confianza media o alta', () => {
      const result = detectColombianRegion(1.0, -77.5);
      expect(result.isInColombia).toBe(true);
      expect(['alta', 'media']).toContain(result.confidence);
    });
  });

  describe('COLOMBIAN_REGION_OPTIONS', () => {
    it('Tiene exactamente 6 regiones', () => {
      expect(COLOMBIAN_REGION_OPTIONS).toHaveLength(6);
    });

    it('Cada opción tiene key, label y cities', () => {
      for (const opt of COLOMBIAN_REGION_OPTIONS) {
        expect(opt).toHaveProperty('key');
        expect(opt).toHaveProperty('label');
        expect(opt).toHaveProperty('cities');
        expect(opt.cities.length).toBeGreaterThan(0);
      }
    });
  });
});
