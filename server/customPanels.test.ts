/**
 * Tests unitarios para procedimientos tRPC de paneles personalizados
 * Verifica la validación de entrada y la estructura de los schemas
 */
import { describe, it, expect } from 'vitest';
import { z } from 'zod';

// Schema de creación (replica la validación del router)
const createPanelSchema = z.object({
  name: z.string().min(1).max(255),
  powerRating: z.number().positive(),
  efficiency: z.number().min(0).max(100),
  tempCoeff: z.number(),
  noct: z.number().min(30).max(80),
  area: z.number().positive(),
  degradationAnnual: z.number().min(0).max(5),
  voc: z.number().optional(),
  isc: z.number().optional(),
  vmp: z.number().optional(),
  imp: z.number().optional(),
  lengthMm: z.number().optional(),
  widthMm: z.number().optional(),
  weightKg: z.number().optional(),
  systemLoss: z.number().optional(),
  application: z.string().optional(),
});

const updatePanelSchema = z.object({
  id: z.number(),
  name: z.string().min(1).max(255).optional(),
  powerRating: z.number().positive().optional(),
  efficiency: z.number().min(0).max(100).optional(),
  tempCoeff: z.number().optional(),
  noct: z.number().min(30).max(80).optional(),
  area: z.number().positive().optional(),
  degradationAnnual: z.number().min(0).max(5).optional(),
  voc: z.number().optional(),
  isc: z.number().optional(),
  vmp: z.number().optional(),
  imp: z.number().optional(),
  lengthMm: z.number().optional(),
  widthMm: z.number().optional(),
  weightKg: z.number().optional(),
  systemLoss: z.number().optional(),
  application: z.string().optional(),
});

const deletePanelSchema = z.object({ id: z.number() });

describe('Custom Panels - Schema Validation', () => {
  describe('createPanelSchema', () => {
    it('acepta datos válidos completos', () => {
      const valid = {
        name: 'Panel BIPV Test',
        powerRating: 400,
        efficiency: 20.5,
        tempCoeff: -0.36,
        noct: 45,
        area: 1.7,
        degradationAnnual: 0.5,
        voc: 48.5,
        isc: 10.2,
        vmp: 40.1,
        imp: 9.8,
        lengthMm: 1700,
        widthMm: 1000,
        weightKg: 22,
        systemLoss: 14,
        application: 'Fachada ventilada',
      };
      const result = createPanelSchema.safeParse(valid);
      expect(result.success).toBe(true);
    });

    it('acepta datos mínimos requeridos', () => {
      const minimal = {
        name: 'Panel Mínimo',
        powerRating: 100,
        efficiency: 15,
        tempCoeff: -0.4,
        noct: 45,
        area: 1.0,
        degradationAnnual: 0.5,
      };
      const result = createPanelSchema.safeParse(minimal);
      expect(result.success).toBe(true);
    });

    it('rechaza nombre vacío', () => {
      const invalid = {
        name: '',
        powerRating: 400,
        efficiency: 20.5,
        tempCoeff: -0.36,
        noct: 45,
        area: 1.7,
        degradationAnnual: 0.5,
      };
      const result = createPanelSchema.safeParse(invalid);
      expect(result.success).toBe(false);
    });

    it('rechaza powerRating negativo', () => {
      const invalid = {
        name: 'Panel',
        powerRating: -100,
        efficiency: 20.5,
        tempCoeff: -0.36,
        noct: 45,
        area: 1.7,
        degradationAnnual: 0.5,
      };
      const result = createPanelSchema.safeParse(invalid);
      expect(result.success).toBe(false);
    });

    it('rechaza efficiency > 100', () => {
      const invalid = {
        name: 'Panel',
        powerRating: 400,
        efficiency: 150,
        tempCoeff: -0.36,
        noct: 45,
        area: 1.7,
        degradationAnnual: 0.5,
      };
      const result = createPanelSchema.safeParse(invalid);
      expect(result.success).toBe(false);
    });

    it('rechaza NOCT fuera de rango (< 30)', () => {
      const invalid = {
        name: 'Panel',
        powerRating: 400,
        efficiency: 20,
        tempCoeff: -0.36,
        noct: 20,
        area: 1.7,
        degradationAnnual: 0.5,
      };
      const result = createPanelSchema.safeParse(invalid);
      expect(result.success).toBe(false);
    });

    it('rechaza NOCT fuera de rango (> 80)', () => {
      const invalid = {
        name: 'Panel',
        powerRating: 400,
        efficiency: 20,
        tempCoeff: -0.36,
        noct: 90,
        area: 1.7,
        degradationAnnual: 0.5,
      };
      const result = createPanelSchema.safeParse(invalid);
      expect(result.success).toBe(false);
    });

    it('rechaza degradación > 5%', () => {
      const invalid = {
        name: 'Panel',
        powerRating: 400,
        efficiency: 20,
        tempCoeff: -0.36,
        noct: 45,
        area: 1.7,
        degradationAnnual: 6,
      };
      const result = createPanelSchema.safeParse(invalid);
      expect(result.success).toBe(false);
    });

    it('rechaza área negativa', () => {
      const invalid = {
        name: 'Panel',
        powerRating: 400,
        efficiency: 20,
        tempCoeff: -0.36,
        noct: 45,
        area: -1,
        degradationAnnual: 0.5,
      };
      const result = createPanelSchema.safeParse(invalid);
      expect(result.success).toBe(false);
    });

    it('acepta tempCoeff positivo (caso CdTe)', () => {
      const valid = {
        name: 'Panel CdTe',
        powerRating: 120,
        efficiency: 12,
        tempCoeff: 0.1,
        noct: 42,
        area: 1.2,
        degradationAnnual: 0.6,
      };
      const result = createPanelSchema.safeParse(valid);
      expect(result.success).toBe(true);
    });

    it('nombre máximo 255 caracteres', () => {
      const longName = 'A'.repeat(256);
      const invalid = {
        name: longName,
        powerRating: 400,
        efficiency: 20,
        tempCoeff: -0.36,
        noct: 45,
        area: 1.7,
        degradationAnnual: 0.5,
      };
      const result = createPanelSchema.safeParse(invalid);
      expect(result.success).toBe(false);
    });
  });

  describe('updatePanelSchema', () => {
    it('acepta actualización parcial (solo nombre)', () => {
      const result = updatePanelSchema.safeParse({ id: 1, name: 'Nuevo Nombre' });
      expect(result.success).toBe(true);
    });

    it('acepta actualización parcial (solo powerRating)', () => {
      const result = updatePanelSchema.safeParse({ id: 1, powerRating: 500 });
      expect(result.success).toBe(true);
    });

    it('requiere id', () => {
      const result = updatePanelSchema.safeParse({ name: 'Test' });
      expect(result.success).toBe(false);
    });

    it('rechaza id no numérico', () => {
      const result = updatePanelSchema.safeParse({ id: 'abc', name: 'Test' });
      expect(result.success).toBe(false);
    });

    it('acepta actualización completa', () => {
      const result = updatePanelSchema.safeParse({
        id: 5,
        name: 'Panel Actualizado',
        powerRating: 450,
        efficiency: 22,
        tempCoeff: -0.35,
        noct: 43,
        area: 1.8,
        degradationAnnual: 0.4,
      });
      expect(result.success).toBe(true);
    });
  });

  describe('deletePanelSchema', () => {
    it('acepta id válido', () => {
      const result = deletePanelSchema.safeParse({ id: 1 });
      expect(result.success).toBe(true);
    });

    it('rechaza sin id', () => {
      const result = deletePanelSchema.safeParse({});
      expect(result.success).toBe(false);
    });

    it('rechaza id string', () => {
      const result = deletePanelSchema.safeParse({ id: 'abc' });
      expect(result.success).toBe(false);
    });
  });
});

describe('Custom Panels - Data Integrity', () => {
  it('valores típicos de panel BIPV colombiano pasan validación', () => {
    // Panel HIITIO TOPCon típico
    const hiitioPanel = {
      name: 'HIITIO TOPCon Flex 430W',
      powerRating: 430,
      efficiency: 22.1,
      tempCoeff: -0.30,
      noct: 43,
      area: 1.95,
      degradationAnnual: 0.4,
      voc: 51.2,
      isc: 10.8,
      vmp: 43.1,
      imp: 10.0,
      lengthMm: 1762,
      widthMm: 1134,
      weightKg: 4.5,
      systemLoss: 12,
      application: 'Cubierta flexible BIPV',
    };
    const result = createPanelSchema.safeParse(hiitioPanel);
    expect(result.success).toBe(true);
  });

  it('valores típicos de panel EINNOVA pasan validación', () => {
    const einnovaPanel = {
      name: 'EINNOVA Vidrio Doble 200W',
      powerRating: 200,
      efficiency: 11.5,
      tempCoeff: -0.38,
      noct: 47,
      area: 1.74,
      degradationAnnual: 0.5,
      voc: 37.8,
      isc: 6.9,
      vmp: 31.2,
      imp: 6.4,
      lengthMm: 1580,
      widthMm: 1100,
      weightKg: 28,
      systemLoss: 16,
      application: 'Lucernario vidrio doble',
    };
    const result = createPanelSchema.safeParse(einnovaPanel);
    expect(result.success).toBe(true);
  });

  it('panel CdTe semitransparente con baja eficiencia pasa validación', () => {
    const cdtePanel = {
      name: 'CdTe Semitransparente 80W',
      powerRating: 80,
      efficiency: 8.5,
      tempCoeff: -0.20,
      noct: 42,
      area: 0.94,
      degradationAnnual: 0.6,
      application: 'Fachada semitransparente',
    };
    const result = createPanelSchema.safeParse(cdtePanel);
    expect(result.success).toBe(true);
  });
});
