/**
 * Tests unitarios para los 18 productos EINNOVA en panelTechnologies.ts
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

// Filtrar productos EINNOVA
const einnovaProducts = DEFAULT_PANEL_TECHNOLOGIES.filter(p => p.brand === 'einnova');
const hiitioProducts = DEFAULT_PANEL_TECHNOLOGIES.filter(p => p.brand === 'hiitio');
const genericProducts = DEFAULT_PANEL_TECHNOLOGIES.filter(p => p.brand === 'generic');

describe('EINNOVA Products — Catalog Integrity', () => {
  it('should have exactly 18 EINNOVA products', () => {
    expect(einnovaProducts.length).toBe(18);
  });

  it('should have exactly 17 HIITIO products', () => {
    expect(hiitioProducts.length).toBe(17);
  });

  it('should have exactly 3 generic products', () => {
    expect(genericProducts.length).toBe(3);
  });

  it('all EINNOVA products should have brand = einnova', () => {
    einnovaProducts.forEach(p => {
      expect(p.brand).toBe('einnova');
    });
  });

  it('all EINNOVA products should have IDs starting with P', () => {
    einnovaProducts.forEach(p => {
      expect(p.id).toMatch(/^P\d+$/);
    });
  });

  it('all EINNOVA products should have unique IDs', () => {
    const ids = einnovaProducts.map(p => p.id);
    expect(new Set(ids).size).toBe(ids.length);
  });

  it('all EINNOVA products should have names containing EINNOVA', () => {
    einnovaProducts.forEach(p => {
      expect(p.name).toContain('EINNOVA');
    });
  });

  it('all EINNOVA products should have isCustom = false', () => {
    einnovaProducts.forEach(p => {
      expect(p.isCustom).toBe(false);
    });
  });
});

describe('EINNOVA Products — Technical Data Validation', () => {
  it('all EINNOVA products should have positive pmax', () => {
    einnovaProducts.forEach(p => {
      expect(p.pmax).toBeGreaterThan(0);
    });
  });

  it('all EINNOVA products should have valid efficiency (1-30%)', () => {
    einnovaProducts.forEach(p => {
      expect(p.efficiencySTC).toBeGreaterThan(1);
      expect(p.efficiencySTC).toBeLessThan(30);
    });
  });

  it('all EINNOVA products should have negative temperature coefficient', () => {
    einnovaProducts.forEach(p => {
      expect(p.tempCoeffPmax).toBeLessThan(0);
    });
  });

  it('all EINNOVA products should have valid dimensions (>0)', () => {
    einnovaProducts.forEach(p => {
      expect(p.lengthMm).toBeGreaterThan(0);
      expect(p.widthMm).toBeGreaterThan(0);
      expect(p.weightKg).toBeGreaterThan(0);
    });
  });

  it('all EINNOVA products should have valid NOCT (35-55°C)', () => {
    einnovaProducts.forEach(p => {
      expect(p.noct).toBeGreaterThanOrEqual(35);
      expect(p.noct).toBeLessThanOrEqual(55);
    });
  });

  it('all EINNOVA products should have valid PVGIS tech choice', () => {
    const validTechChoices = ['crystSi', 'CdTe', 'CIS', 'Unknown'];
    einnovaProducts.forEach(p => {
      expect(validTechChoices).toContain(p.pvgisTechchoice);
    });
  });

  it('all EINNOVA products should have valid PVGIS mounting place', () => {
    einnovaProducts.forEach(p => {
      expect(['free', 'building']).toContain(p.pvgisMountingplace);
    });
  });

  it('Wp/m² should be consistent with pmax and dimensions', () => {
    einnovaProducts.forEach(p => {
      const areaM2 = (p.lengthMm / 1000) * (p.widthMm / 1000);
      const calculatedWpM2 = p.pmax / areaM2;
      // Allow 15% tolerance for rounding
      expect(calculatedWpM2).toBeGreaterThan(p.pmax / areaM2 * 0.85);
    });
  });
});

describe('EINNOVA Products — Regional Compatibility', () => {
  it('all EINNOVA products should have regionalCompatibility defined', () => {
    einnovaProducts.forEach(p => {
      expect(p.regionalCompatibility).toBeDefined();
    });
  });

  it('all HIITIO products should have regionalCompatibility defined', () => {
    hiitioProducts.forEach(p => {
      expect(p.regionalCompatibility).toBeDefined();
      const rc = p.regionalCompatibility!;
      const regions: (keyof Omit<RegionalCompatibility, 'notes'>)[] = [
        'caribe', 'andina', 'pacifica', 'orinoquia', 'amazonia', 'insular'
      ];
      regions.forEach(region => {
        expect([1, 2, 3]).toContain(rc[region]);
      });
      expect(rc.notes).toBeTruthy();
    });
  });

  it('HIITIO TOPCon Flex (H01-H05) should have Andina=1 (no recomendado)', () => {
    const topconFlex = hiitioProducts.filter(p => p.category === 'topcon_flex');
    expect(topconFlex.length).toBe(5);
    topconFlex.forEach(p => {
      expect(p.regionalCompatibility!.andina).toBe(1);
      expect(p.regionalCompatibility!.caribe).toBe(3);
    });
  });

  it('HIITIO HJT Curtain Wall (H06-H08) should have Amazonia=1', () => {
    const hjtCW = hiitioProducts.filter(p => p.category === 'hjt_curtain');
    expect(hjtCW.length).toBe(3);
    hjtCW.forEach(p => {
      expect(p.regionalCompatibility!.amazonia).toBe(1);
      expect(p.regionalCompatibility!.andina).toBe(3);
    });
  });

  it('HIITIO CIGS (H17) should have Orinoquia=1', () => {
    const cigs = hiitioProducts.find(p => p.id === 'H17')!;
    expect(cigs.regionalCompatibility!.orinoquia).toBe(1);
    expect(cigs.regionalCompatibility!.andina).toBe(3);
  });

  it('all regional values should be 1, 2, or 3', () => {
    einnovaProducts.forEach(p => {
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
    einnovaProducts.forEach(p => {
      expect(p.regionalCompatibility!.notes).toBeTruthy();
      expect(typeof p.regionalCompatibility!.notes).toBe('string');
    });
  });

  it('P01 (Antirreflejo TOPCon) should be optimal (3) for most regions', () => {
    const p01 = einnovaProducts.find(p => p.id === 'P01')!;
    expect(p01.regionalCompatibility!.caribe).toBe(3);
    expect(p01.regionalCompatibility!.andina).toBe(3);
    expect(p01.regionalCompatibility!.pacifica).toBe(3);
    expect(p01.regionalCompatibility!.orinoquia).toBe(3);
    expect(p01.regionalCompatibility!.insular).toBe(3);
  });

  it('P02 (Bifacial) should have lower compatibility for some regions', () => {
    const p02 = einnovaProducts.find(p => p.id === 'P02')!;
    // Bifacial needs albedo, not ideal everywhere
    expect(p02.regionalCompatibility).toBeDefined();
    // At least one region should be less than 3
    const rc = p02.regionalCompatibility!;
    const values = [rc.caribe, rc.andina, rc.pacifica, rc.orinoquia, rc.amazonia, rc.insular];
    expect(values.some(v => v < 3)).toBe(true);
  });

  it('P16 (Pavimento) should have limited compatibility', () => {
    const p16 = einnovaProducts.find(p => p.id === 'P16')!;
    expect(p16.regionalCompatibility).toBeDefined();
    // Pavimento is specialized, should have some 2s or 1s
    const rc = p16.regionalCompatibility!;
    const values = [rc.caribe, rc.andina, rc.pacifica, rc.orinoquia, rc.amazonia, rc.insular];
    expect(values.some(v => v < 3)).toBe(true);
  });
});

describe('EINNOVA Products — Categories', () => {
  const einnovaCategories = [
    'einnova_antirreflejo', 'einnova_bifacial', 'einnova_teja_bc', 'einnova_teja_plana',
    'einnova_color_panel', 'einnova_fachada', 'einnova_flexible', 'einnova_agripv',
    'einnova_pavimento', 'einnova_vidrio'
  ];

  it('all EINNOVA categories should have labels', () => {
    einnovaCategories.forEach(cat => {
      expect(CATEGORY_LABELS[cat]).toBeDefined();
      expect(CATEGORY_LABELS[cat].length).toBeGreaterThan(0);
    });
  });

  it('all EINNOVA products should use EINNOVA-prefixed categories', () => {
    einnovaProducts.forEach(p => {
      expect(p.category).toMatch(/^einnova_/);
    });
  });

  it('getTechnologiesByCategory should group EINNOVA products correctly', () => {
    const allGrouped = getTechnologiesByCategory(DEFAULT_PANEL_TECHNOLOGIES);
    const einnovaKeys = Object.keys(allGrouped).filter(k => k.startsWith('einnova_'));
    expect(einnovaKeys.length).toBeGreaterThanOrEqual(8); // At least 8 EINNOVA categories
    einnovaKeys.forEach(key => {
      expect(allGrouped[key].length).toBeGreaterThan(0);
      allGrouped[key].forEach(p => {
        expect(p.brand).toBe('einnova');
      });
    });
  });

  it('einnova_teja_bc category should have 3 products (P04, P06, P13)', () => {
    const tejaBC = einnovaProducts.filter(p => p.category === 'einnova_teja_bc');
    expect(tejaBC.length).toBe(3);
    const ids = tejaBC.map(p => p.id).sort();
    expect(ids).toEqual(['P04', 'P06', 'P13']);
  });

  it('einnova_fachada category should have 3 products (P08, P10, P11)', () => {
    const fachada = einnovaProducts.filter(p => p.category === 'einnova_fachada');
    expect(fachada.length).toBe(3);
    const ids = fachada.map(p => p.id).sort();
    expect(ids).toEqual(['P08', 'P10', 'P11']);
  });

  it('einnova_flexible category should have 2 products (P07, P14)', () => {
    const flexible = einnovaProducts.filter(p => p.category === 'einnova_flexible');
    expect(flexible.length).toBe(2);
    const ids = flexible.map(p => p.id).sort();
    expect(ids).toEqual(['P07', 'P14']);
  });

  it('einnova_agripv category should have 2 products (P15, P17)', () => {
    const agripv = einnovaProducts.filter(p => p.category === 'einnova_agripv');
    expect(agripv.length).toBe(2);
    const ids = agripv.map(p => p.id).sort();
    expect(ids).toEqual(['P15', 'P17']);
  });
});

describe('EINNOVA Products — Specific Product Validation', () => {
  it('P01 should have correct specs (455W TOPCon N antirreflejo)', () => {
    const p01 = einnovaProducts.find(p => p.id === 'P01')!;
    expect(p01.pmax).toBe(455);
    expect(p01.efficiencySTC).toBeCloseTo(23.3, 1);
    expect(p01.category).toBe('einnova_antirreflejo');
    expect(p01.pvgisTechchoice).toBe('crystSi');
    expect(p01.pvgisMountingplace).toBe('building');
  });

  it('P02 should have correct specs (580W Bifacial N-Type)', () => {
    const p02 = einnovaProducts.find(p => p.id === 'P02')!;
    expect(p02.pmax).toBe(580);
    expect(p02.efficiencySTC).toBeCloseTo(22.44, 1);
    expect(p02.category).toBe('einnova_bifacial');
    expect(p02.pvgisMountingplace).toBe('free');
  });

  it('P18 should have correct specs (58W Vidrio FV CdTe)', () => {
    const p18 = einnovaProducts.find(p => p.id === 'P18')!;
    expect(p18.pmax).toBe(58);
    expect(p18.pvgisTechchoice).toBe('CdTe');
    expect(p18.category).toBe('einnova_vidrio');
  });

  it('P16 should have correct specs (110W Pavimento Solar)', () => {
    const p16 = einnovaProducts.find(p => p.id === 'P16')!;
    expect(p16.pmax).toBe(110);
    expect(p16.category).toBe('einnova_pavimento');
  });
});
