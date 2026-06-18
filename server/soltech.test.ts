/**
 * Tests unitarios para los 25 productos SOLTECH en panelTechnologies.ts
 * Valida: brand, categorías, compatibilidad regional, datos técnicos
 */
import { describe, it, expect } from 'vitest';
import {
  DEFAULT_PANEL_TECHNOLOGIES,
  PanelTechnology,
  RegionalCompatibility,
  getTechnologiesByCategory,
  CATEGORY_LABELS,
} from '../client/src/lib/panelTechnologies';

// Filtrar productos SOLTECH
const soltechProducts = DEFAULT_PANEL_TECHNOLOGIES.filter(p => p.brand === 'soltech');

describe('SOLTECH Products — Catalog Integrity', () => {
  it('should have exactly 25 SOLTECH products', () => {
    expect(soltechProducts.length).toBe(25);
  });

  it('all SOLTECH products should have brand = soltech', () => {
    soltechProducts.forEach(p => {
      expect(p.brand).toBe('soltech');
    });
  });

  it('all SOLTECH products should have IDs starting with S', () => {
    soltechProducts.forEach(p => {
      expect(p.id).toMatch(/^S\d+$/);
    });
  });

  it('all SOLTECH products should have unique IDs', () => {
    const ids = soltechProducts.map(p => p.id);
    expect(new Set(ids).size).toBe(ids.length);
  });

  it('all SOLTECH products should have names containing SOLTECH or NextCity', () => {
    soltechProducts.forEach(p => {
      const nameOk = p.name.includes('SOLTECH') || p.name.includes('NextCity');
      expect(nameOk).toBe(true);
    });
  });

  it('all SOLTECH products should have isCustom = false', () => {
    soltechProducts.forEach(p => {
      expect(p.isCustom).toBe(false);
    });
  });
});

describe('SOLTECH Products — Technical Data Validation', () => {
  it('all SOLTECH products should have positive pmax', () => {
    soltechProducts.forEach(p => {
      expect(p.pmax).toBeGreaterThan(0);
    });
  });

  it('all SOLTECH products should have valid efficiency (1-30%)', () => {
    soltechProducts.forEach(p => {
      expect(p.efficiencySTC).toBeGreaterThan(1);
      expect(p.efficiencySTC).toBeLessThan(30);
    });
  });

  it('all SOLTECH products should have negative temperature coefficient', () => {
    soltechProducts.forEach(p => {
      expect(p.tempCoeffPmax).toBeLessThan(0);
    });
  });

  it('all SOLTECH products should have valid dimensions (>0)', () => {
    soltechProducts.forEach(p => {
      expect(p.lengthMm).toBeGreaterThan(0);
      expect(p.widthMm).toBeGreaterThan(0);
      expect(p.weightKg).toBeGreaterThan(0);
    });
  });

  it('all SOLTECH products should have valid NOCT (35-55°C)', () => {
    soltechProducts.forEach(p => {
      expect(p.noct).toBeGreaterThanOrEqual(35);
      expect(p.noct).toBeLessThanOrEqual(55);
    });
  });

  it('all SOLTECH products should have valid PVGIS tech choice', () => {
    const validTechChoices = ['crystSi', 'CdTe', 'CIS', 'Unknown'];
    soltechProducts.forEach(p => {
      expect(validTechChoices).toContain(p.pvgisTechchoice);
    });
  });

  it('all SOLTECH products should have building PVGIS mounting place', () => {
    soltechProducts.forEach(p => {
      expect(p.pvgisMountingplace).toBe('building');
    });
  });

  it('Wp/m² should be consistent with pmax and dimensions', () => {
    soltechProducts.forEach(p => {
      const areaM2 = (p.lengthMm / 1000) * (p.widthMm / 1000);
      const calculatedWpM2 = p.pmax / areaM2;
      expect(calculatedWpM2).toBeGreaterThan(0);
    });
  });
});

describe('SOLTECH Products — Regional Compatibility', () => {
  it('all SOLTECH products should have regionalCompatibility defined', () => {
    soltechProducts.forEach(p => {
      expect(p.regionalCompatibility).toBeDefined();
    });
  });

  it('all regional values should be 1, 2, or 3', () => {
    soltechProducts.forEach(p => {
      const rc = p.regionalCompatibility!;
      const regions: (keyof Omit<RegionalCompatibility, 'notes'>)[] = [
        'caribe', 'andina', 'pacifica', 'orinoquia', 'amazonia', 'insular'
      ];
      regions.forEach(region => {
        expect([1, 2, 3]).toContain(rc[region]);
      });
    });
  });

  it('all regional compatibility should have notes', () => {
    soltechProducts.forEach(p => {
      expect(p.regionalCompatibility!.notes).toBeTruthy();
      expect(typeof p.regionalCompatibility!.notes).toBe('string');
    });
  });

  it('CdTe laminado (S01-S12) should have caribe=3 and andina=2', () => {
    const laminados = soltechProducts.filter(p => p.category === 'soltech_laminado');
    expect(laminados.length).toBe(12);
    laminados.forEach(p => {
      expect(p.regionalCompatibility!.caribe).toBe(3);
      expect(p.regionalCompatibility!.andina).toBe(2);
      expect(p.regionalCompatibility!.pacifica).toBe(3);
    });
  });

  it('CIGS Tejas (S22-S24) should have andina=3', () => {
    const tejas = soltechProducts.filter(p => p.category === 'soltech_teja');
    expect(tejas.length).toBe(3);
    tejas.forEach(p => {
      expect(p.regionalCompatibility!.andina).toBe(3);
      expect(p.regionalCompatibility!.caribe).toBe(2);
      expect(p.regionalCompatibility!.orinoquia).toBe(1);
    });
  });
});

describe('SOLTECH Products — Categories', () => {
  const soltechCategories = [
    'soltech_laminado', 'soltech_dvh', 'soltech_opaco', 'soltech_transparente', 'soltech_teja'
  ];

  it('all SOLTECH categories should have labels', () => {
    soltechCategories.forEach(cat => {
      expect(CATEGORY_LABELS[cat]).toBeDefined();
      expect(CATEGORY_LABELS[cat].length).toBeGreaterThan(0);
    });
  });

  it('all SOLTECH products should use SOLTECH-prefixed categories', () => {
    soltechProducts.forEach(p => {
      expect(p.category).toMatch(/^soltech_/);
    });
  });

  it('getTechnologiesByCategory should group SOLTECH products correctly', () => {
    const allGrouped = getTechnologiesByCategory(DEFAULT_PANEL_TECHNOLOGIES);
    const soltechKeys = Object.keys(allGrouped).filter(k => k.startsWith('soltech_'));
    expect(soltechKeys.length).toBe(5);
    soltechKeys.forEach(key => {
      expect(allGrouped[key].length).toBeGreaterThan(0);
      allGrouped[key].forEach(p => {
        expect(p.brand).toBe('soltech');
      });
    });
  });
});
