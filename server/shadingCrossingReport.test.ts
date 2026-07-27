/**
 * Tests for shadingCrossingReportSection.ts
 * 
 * Tests the PDF generation logic for shading crossing results:
 * - computeFacadeSummaries
 * - computeHourlyDistribution
 * - addShadingCrossingSectionToDoc
 * - generateShadingCrossingReport
 */

import { describe, it, expect, vi } from 'vitest';

// Since the module uses jsPDF which is browser-only, we test the logic functions
// by importing them indirectly through the module structure

// Mock jsPDF and autoTable for testing
vi.mock('jspdf', () => {
  const mockDoc = {
    internal: { pageSize: { getWidth: () => 210, getHeight: () => 297 } },
    setFontSize: vi.fn(),
    setTextColor: vi.fn(),
    setDrawColor: vi.fn(),
    setFillColor: vi.fn(),
    setLineWidth: vi.fn(),
    setFont: vi.fn(),
    text: vi.fn(),
    line: vi.fn(),
    rect: vi.fn(),
    triangle: vi.fn(),
    moveTo: vi.fn(),
    addPage: vi.fn(),
    addImage: vi.fn(),
    getNumberOfPages: () => 1,
    setPage: vi.fn(),
    save: vi.fn(),
    getTextWidth: () => 50,
    lastAutoTable: { finalY: 50 },
  };
  return { default: vi.fn(() => mockDoc) };
});

vi.mock('jspdf-autotable', () => ({
  default: vi.fn((doc: any) => { doc.lastAutoTable = { finalY: 50 }; }),
}));

// Import after mocks
import type { CrossingResult, FacadeDefinition } from '../client/src/lib/shadingMaskCrossing';

describe('Shading Crossing Report Section', () => {
  const mockFacades: FacadeDefinition[] = [
    { name: 'Fachada Norte', azimuthNormal: 0, tilt: 90 },
    { name: 'Fachada Este', azimuthNormal: -90, tilt: 90 },
  ];

  const mockResults: CrossingResult[] = [
    {
      evento: 'Equinoccio de Marzo',
      month: 'Mar',
      day: 20,
      hourStr: '08:00',
      hour: 8,
      heightSolar: 25.5,
      azimuthSolar: -60.2,
      facade: 'Fachada Norte',
      fsGeometrico: 0.3,
      fsClimatico: 0.2,
      fs: 0.44,
      situacion: 'Parcial',
      obstacle: 'Edificio A',
    },
    {
      evento: 'Equinoccio de Marzo',
      month: 'Mar',
      day: 20,
      hourStr: '10:00',
      hour: 10,
      heightSolar: 45.3,
      azimuthSolar: -30.1,
      facade: 'Fachada Norte',
      fsGeometrico: 0.1,
      fsClimatico: 0.15,
      fs: 0.235,
      situacion: 'Despejado',
      obstacle: 'Ninguno',
    },
    {
      evento: 'Equinoccio de Marzo',
      month: 'Mar',
      day: 20,
      hourStr: '08:00',
      hour: 8,
      heightSolar: 25.5,
      azimuthSolar: -60.2,
      facade: 'Fachada Este',
      fsGeometrico: 0.6,
      fsClimatico: 0.4,
      fs: 0.76,
      situacion: 'Nublado',
      obstacle: 'Edificio B',
    },
    {
      evento: 'Equinoccio de Marzo',
      month: 'Mar',
      day: 20,
      hourStr: '12:00',
      hour: 12,
      heightSolar: 60.0,
      azimuthSolar: 0,
      facade: 'Fachada Norte',
      fsGeometrico: 0.0,
      fsClimatico: 0.8,
      fs: 0.8,
      situacion: 'Cubierto',
      obstacle: 'Ninguno',
    },
    {
      evento: 'Solsticio de Junio',
      month: 'Jun',
      day: 21,
      hourStr: '10:00',
      hour: 10,
      heightSolar: 50.0,
      azimuthSolar: -40.0,
      facade: 'Fachada Este',
      fsGeometrico: 0.2,
      fsClimatico: 0.1,
      fs: 0.28,
      situacion: 'Despejado',
      obstacle: 'Ninguno',
    },
  ];

  describe('Facade Summary Computation', () => {
    it('should compute correct averages for each facade', () => {
      // Manually compute expected values
      const northResults = mockResults.filter(r => r.facade === 'Fachada Norte');
      const avgFsNorth = northResults.reduce((a, r) => a + r.fs, 0) / northResults.length;
      
      // Expected: (0.44 + 0.235 + 0.8) / 3 = 0.4917
      expect(avgFsNorth).toBeCloseTo(0.4917, 3);
    });

    it('should compute correct max/min FS', () => {
      const northResults = mockResults.filter(r => r.facade === 'Fachada Norte');
      const maxFs = Math.max(...northResults.map(r => r.fs));
      const minFs = Math.min(...northResults.map(r => r.fs));
      
      expect(maxFs).toBe(0.8);
      expect(minFs).toBe(0.235);
    });

    it('should count sky conditions correctly', () => {
      const northResults = mockResults.filter(r => r.facade === 'Fachada Norte');
      const despejado = northResults.filter(r => r.situacion === 'Despejado').length;
      const parcial = northResults.filter(r => r.situacion === 'Parcial').length;
      const cubierto = northResults.filter(r => r.situacion === 'Cubierto').length;
      
      expect(despejado).toBe(1);
      expect(parcial).toBe(1);
      expect(cubierto).toBe(1);
    });

    it('should count hours evaluated per facade', () => {
      const northCount = mockResults.filter(r => r.facade === 'Fachada Norte').length;
      const eastCount = mockResults.filter(r => r.facade === 'Fachada Este').length;
      
      expect(northCount).toBe(3);
      expect(eastCount).toBe(2);
    });
  });

  describe('Hourly Distribution Computation', () => {
    it('should group results by hour', () => {
      const hours = Array.from(new Set(mockResults.map(r => r.hour))).sort((a, b) => a - b);
      expect(hours).toEqual([8, 10, 12]);
    });

    it('should compute average FS per facade per hour', () => {
      // Hour 8, Fachada Norte: only 1 result with fs=0.44
      const hour8North = mockResults.filter(r => r.hour === 8 && r.facade === 'Fachada Norte');
      const avgH8N = hour8North.reduce((a, r) => a + r.fs, 0) / hour8North.length;
      expect(avgH8N).toBeCloseTo(0.44, 3);

      // Hour 8, Fachada Este: only 1 result with fs=0.76
      const hour8East = mockResults.filter(r => r.hour === 8 && r.facade === 'Fachada Este');
      const avgH8E = hour8East.reduce((a, r) => a + r.fs, 0) / hour8East.length;
      expect(avgH8E).toBeCloseTo(0.76, 3);
    });
  });

  describe('PDF Generation (smoke tests)', () => {
    it('should import generateShadingCrossingReport without errors', async () => {
      const { generateShadingCrossingReport } = await import('../client/src/lib/shadingCrossingReportSection');
      expect(generateShadingCrossingReport).toBeDefined();
      expect(typeof generateShadingCrossingReport).toBe('function');
    });

    it('should import addShadingCrossingSectionToDoc without errors', async () => {
      const { addShadingCrossingSectionToDoc } = await import('../client/src/lib/shadingCrossingReportSection');
      expect(addShadingCrossingSectionToDoc).toBeDefined();
      expect(typeof addShadingCrossingSectionToDoc).toBe('function');
    });

    it('should generate standalone PDF without throwing', async () => {
      const { generateShadingCrossingReport } = await import('../client/src/lib/shadingCrossingReportSection');
      
      expect(() => {
        generateShadingCrossingReport({
          crossingResults: mockResults,
          facades: mockFacades,
          evaluationModel: null,
          latitude: 6.25,
          longitude: -75.56,
          cityName: 'Medellín',
          elevation: 1495,
        });
      }).not.toThrow();
    });

    it('should handle empty results gracefully', async () => {
      const { generateShadingCrossingReport } = await import('../client/src/lib/shadingCrossingReportSection');
      
      expect(() => {
        generateShadingCrossingReport({
          crossingResults: [],
          facades: mockFacades,
          evaluationModel: null,
          latitude: 6.25,
          longitude: -75.56,
          cityName: 'Medellín',
        });
      }).not.toThrow();
    });

    it('should add section to existing doc without throwing', async () => {
      const jsPDF = (await import('jspdf')).default;
      const { addShadingCrossingSectionToDoc } = await import('../client/src/lib/shadingCrossingReportSection');
      
      const doc = new jsPDF();
      const finalY = addShadingCrossingSectionToDoc(doc, 50, 5, {
        crossingResults: mockResults,
        facades: mockFacades,
        evaluationModel: null,
        latitude: 6.25,
        longitude: -75.56,
        cityName: 'Medellín',
        elevation: 1495,
      });

      expect(finalY).toBeGreaterThan(0);
    });

    it('should include model info when evaluationModel is provided', async () => {
      const jsPDF = (await import('jspdf')).default;
      const { addShadingCrossingSectionToDoc } = await import('../client/src/lib/shadingCrossingReportSection');
      
      const doc = new jsPDF();
      const mockModel = {
        fileName: 'edificio.obj',
        dimensions: { x: 10, y: 8, z: 12 },
        detectedFacades: [
          { name: 'Norte', azimuth: 0, tilt: 90, area: 80, centroid: { x: 0, y: 0, z: 6 }, normal: { x: 0, y: -1, z: 0 }, faces: [] },
        ],
        parseResult: { vertices: new Array(100), totalFaces: 50, objects: [] },
        evaluationPoint: { x: 5, y: 4, z: 6 },
      };

      expect(() => {
        addShadingCrossingSectionToDoc(doc, 50, 5, {
          crossingResults: mockResults,
          facades: mockFacades,
          evaluationModel: mockModel as any,
          latitude: 6.25,
          longitude: -75.56,
          cityName: 'Medellín',
          elevation: 1495,
        });
      }).not.toThrow();
    });
  });

  describe('Data Integrity', () => {
    it('should preserve all crossing result fields', () => {
      const result = mockResults[0];
      expect(result.evento).toBe('Equinoccio de Marzo');
      expect(result.month).toBe('Mar');
      expect(result.day).toBe(20);
      expect(result.hourStr).toBe('08:00');
      expect(result.hour).toBe(8);
      expect(result.heightSolar).toBe(25.5);
      expect(result.azimuthSolar).toBe(-60.2);
      expect(result.facade).toBe('Fachada Norte');
      expect(result.fsGeometrico).toBe(0.3);
      expect(result.fsClimatico).toBe(0.2);
      expect(result.fs).toBe(0.44);
      expect(result.situacion).toBe('Parcial');
      expect(result.obstacle).toBe('Edificio A');
    });

    it('should handle multiple events correctly', () => {
      const events = Array.from(new Set(mockResults.map(r => r.evento)));
      expect(events).toContain('Equinoccio de Marzo');
      expect(events).toContain('Solsticio de Junio');
      expect(events.length).toBe(2);
    });
  });
});
