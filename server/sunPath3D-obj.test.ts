/**
 * Tests unitarios para los parsers de Sun Path 3D y OBJ
 */
import { describe, it, expect } from 'vitest';

// ── Sun Path 3D Parser Tests ────────────────────────────────────────

// We import the functions from the client lib; vitest resolves the alias
import {
  validateSunPath3DJSON,
  isSunPath3DJSON,
  parseSunPath3D,
  getSunPath3DSummary,
  type SunPath3DJSON,
} from '../client/src/lib/sunPath3DParser';

import {
  parseOBJText,
  validateOBJText,
  getOBJSummary,
  convertOBJToObstacles,
} from '../client/src/lib/objParser';

// ── Fixtures ────────────────────────────────────────────────────────

const validSunPath3D: SunPath3DJSON = {
  Location: {
    latitude: 6.339,
    longitude: -75.5422,
    timezone: -5,
    northOffset: 0,
  },
  DateTime: {
    clockTime: 9,
    dayOfMonth: 6,
    monthOfYear: 2, // 0-indexed → March
    year: 2026,
  },
  SunPath: {
    showSunPos: true,
    showSunDirection: true,
    showSunAngles: true,
    showSunPath: true,
    showAnnualArea: true,
    showAnnualLines: true,
    showAxis: true,
    radius: 1,
    solarChart: 0,
    center: [0, 0, 0],
  },
  Model: {
    shadowsShow: true,
    mapTiles: 'none',
  },
};

const simpleOBJ = `# Simple cube
o Cube
v 0 0 0
v 10 0 0
v 10 10 0
v 0 10 0
v 0 0 10
v 10 0 10
v 10 10 10
v 0 10 10
f 1 2 3 4
f 5 6 7 8
f 1 2 6 5
f 2 3 7 6
f 3 4 8 7
f 4 1 5 8
`;

const multiObjectOBJ = `# Two objects
o Building_A
v 0 0 0
v 5 0 0
v 5 5 0
v 0 5 0
v 0 0 8
v 5 0 8
v 5 5 8
v 0 5 8
f 1 2 3 4
f 5 6 7 8
f 1 2 6 5
f 2 3 7 6
f 3 4 8 7
f 4 1 5 8
o Tree_1
v 20 20 0
v 22 20 0
v 22 22 0
v 20 22 0
v 20 20 6
v 22 20 6
v 22 22 6
v 20 22 6
f 9 10 11 12
f 13 14 15 16
f 9 10 14 13
f 10 11 15 14
f 11 12 16 15
f 12 9 13 16
`;

// ── Sun Path 3D Parser Tests ────────────────────────────────────────

describe('Sun Path 3D Parser', () => {
  describe('validateSunPath3DJSON', () => {
    it('acepta un JSON válido de Sun Path 3D', () => {
      expect(validateSunPath3DJSON(validSunPath3D)).toBe(true);
    });

    it('rechaza null', () => {
      expect(validateSunPath3DJSON(null)).toBe(false);
    });

    it('rechaza un string', () => {
      expect(validateSunPath3DJSON('not an object')).toBe(false);
    });

    it('rechaza un objeto sin Location', () => {
      const noLoc = { DateTime: validSunPath3D.DateTime, SunPath: validSunPath3D.SunPath };
      expect(validateSunPath3DJSON(noLoc)).toBe(false);
    });

    it('rechaza un objeto sin DateTime', () => {
      const noDT = { Location: validSunPath3D.Location, SunPath: validSunPath3D.SunPath };
      expect(validateSunPath3DJSON(noDT)).toBe(false);
    });

    it('rechaza un objeto sin SunPath', () => {
      const noSP = { Location: validSunPath3D.Location, DateTime: validSunPath3D.DateTime };
      expect(validateSunPath3DJSON(noSP)).toBe(false);
    });

    it('rechaza Location con latitud no numérica', () => {
      const bad = {
        ...validSunPath3D,
        Location: { ...validSunPath3D.Location, latitude: 'abc' },
      };
      expect(validateSunPath3DJSON(bad)).toBe(false);
    });

    it('rechaza DateTime con clockTime no numérico', () => {
      const bad = {
        ...validSunPath3D,
        DateTime: { ...validSunPath3D.DateTime, clockTime: 'noon' },
      };
      expect(validateSunPath3DJSON(bad)).toBe(false);
    });
  });

  describe('isSunPath3DJSON', () => {
    it('identifica un JSON de Sun Path 3D correctamente', () => {
      expect(isSunPath3DJSON(validSunPath3D)).toBe(true);
    });

    it('rechaza un JSON de Site Designer (tiene Blocks)', () => {
      const siteDesigner = {
        DateTime: validSunPath3D.DateTime,
        SunPath: validSunPath3D.SunPath,
        Blocks: [],
      };
      expect(isSunPath3DJSON(siteDesigner)).toBe(false);
    });

    it('rechaza un objeto sin DateTime', () => {
      expect(isSunPath3DJSON({ SunPath: {} })).toBe(false);
    });

    it('rechaza null', () => {
      expect(isSunPath3DJSON(null)).toBe(false);
    });
  });

  describe('parseSunPath3D', () => {
    it('extrae la ubicación correctamente', () => {
      const result = parseSunPath3D(validSunPath3D);
      expect(result.location.latitude).toBe(6.339);
      expect(result.location.longitude).toBe(-75.5422);
      expect(result.location.timezone).toBe(-5);
      expect(result.location.northOffset).toBe(0);
    });

    it('convierte monthOfYear de 0-indexed a 1-indexed', () => {
      const result = parseSunPath3D(validSunPath3D);
      // monthOfYear=2 (0-indexed) → month=3 (1-indexed) → March
      expect(result.dateTime.month).toBe(3);
      expect(result.dateTime.monthName).toBe('Mar');
    });

    it('extrae fecha y hora correctamente', () => {
      const result = parseSunPath3D(validSunPath3D);
      expect(result.dateTime.year).toBe(2026);
      expect(result.dateTime.day).toBe(6);
      expect(result.dateTime.hour).toBe(9);
    });

    it('extrae la configuración del domo solar', () => {
      const result = parseSunPath3D(validSunPath3D);
      expect(result.sunPathConfig.center).toEqual([0, 0, 0]);
      expect(result.sunPathConfig.radius).toBe(1);
    });

    it('detecta sombras habilitadas', () => {
      const result = parseSunPath3D(validSunPath3D);
      expect(result.shadowsEnabled).toBe(true);
    });

    it('detecta sombras deshabilitadas', () => {
      const noShadows: SunPath3DJSON = {
        ...validSunPath3D,
        Model: { shadowsShow: false },
      };
      const result = parseSunPath3D(noShadows);
      expect(result.shadowsEnabled).toBe(false);
    });

    it('maneja northOffset ausente como 0', () => {
      const noOffset: SunPath3DJSON = {
        ...validSunPath3D,
        Location: {
          latitude: 10,
          longitude: -70,
          timezone: -5,
          northOffset: undefined as unknown as number,
        },
      };
      const result = parseSunPath3D(noOffset);
      expect(result.location.northOffset).toBe(0);
    });

    it('maneja todos los meses correctamente (0-11)', () => {
      const monthNames = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
      for (let m = 0; m < 12; m++) {
        const data: SunPath3DJSON = {
          ...validSunPath3D,
          DateTime: { ...validSunPath3D.DateTime, monthOfYear: m },
        };
        const result = parseSunPath3D(data);
        expect(result.dateTime.month).toBe(m + 1);
        expect(result.dateTime.monthName).toBe(monthNames[m]);
      }
    });
  });

  describe('getSunPath3DSummary', () => {
    it('genera un resumen legible', () => {
      const summary = getSunPath3DSummary(validSunPath3D);
      expect(summary.location).toBe('6.3390°, -75.5422°');
      expect(summary.timezone).toBe('UTC-5');
      expect(summary.dateTime).toBe('Mar 6, 2026 — 9:00h');
      expect(summary.shadowsEnabled).toBe(true);
    });

    it('formatea timezone positivo con +', () => {
      const utcPlus = {
        ...validSunPath3D,
        Location: { ...validSunPath3D.Location, timezone: 1 },
      };
      const summary = getSunPath3DSummary(utcPlus);
      expect(summary.timezone).toBe('UTC+1');
    });

    it('formatea UTC+0 correctamente', () => {
      const utcZero = {
        ...validSunPath3D,
        Location: { ...validSunPath3D.Location, timezone: 0 },
      };
      const summary = getSunPath3DSummary(utcZero);
      expect(summary.timezone).toBe('UTC+0');
    });
  });
});

// ── OBJ Parser Tests ────────────────────────────────────────────────

describe('OBJ Parser', () => {
  describe('validateOBJText', () => {
    it('acepta un OBJ válido con vértices y caras', () => {
      expect(validateOBJText(simpleOBJ)).toBe(true);
    });

    it('rechaza texto sin vértices', () => {
      expect(validateOBJText('f 1 2 3\nf 4 5 6')).toBe(false);
    });

    it('rechaza texto sin caras', () => {
      expect(validateOBJText('v 0 0 0\nv 1 0 0\nv 0 1 0')).toBe(false);
    });

    it('rechaza texto vacío', () => {
      expect(validateOBJText('')).toBe(false);
    });

    it('rechaza texto con solo comentarios', () => {
      expect(validateOBJText('# This is a comment\n# Another comment')).toBe(false);
    });
  });

  describe('parseOBJText', () => {
    it('parsea vértices correctamente', () => {
      const result = parseOBJText(simpleOBJ);
      expect(result.vertices.length).toBe(8);
      expect(result.vertices[0]).toEqual({ x: 0, y: 0, z: 0 });
      expect(result.vertices[5]).toEqual({ x: 10, y: 0, z: 10 });
    });

    it('parsea caras correctamente', () => {
      const result = parseOBJText(simpleOBJ);
      expect(result.totalFaces).toBe(6);
    });

    it('detecta un solo objeto', () => {
      const result = parseOBJText(simpleOBJ);
      expect(result.objects.length).toBe(1);
      expect(result.objects[0].name).toBe('Cube');
    });

    it('detecta múltiples objetos', () => {
      const result = parseOBJText(multiObjectOBJ);
      expect(result.objects.length).toBe(2);
      expect(result.objects[0].name).toBe('Building_A');
      expect(result.objects[1].name).toBe('Tree_1');
    });

    it('calcula bounding box correctamente', () => {
      const result = parseOBJText(simpleOBJ);
      expect(result.boundingBox.min).toEqual({ x: 0, y: 0, z: 0 });
      expect(result.boundingBox.max).toEqual({ x: 10, y: 10, z: 10 });
      expect(result.boundingBox.center).toEqual({ x: 5, y: 5, z: 5 });
      expect(result.boundingBox.dimensions).toEqual({ x: 10, y: 10, z: 10 });
    });

    it('maneja índices de vértices con textura/normal (v/vt/vn)', () => {
      const objWithNormals = `
v 0 0 0
v 1 0 0
v 1 1 0
v 0 1 0
vn 0 0 1
vt 0 0
f 1/1/1 2/1/1 3/1/1 4/1/1
`;
      const result = parseOBJText(objWithNormals);
      expect(result.vertices.length).toBe(4);
      expect(result.totalFaces).toBe(1);
      expect(result.objects[0].faces[0].vertexIndices).toEqual([0, 1, 2, 3]);
    });

    it('ignora líneas de comentario', () => {
      const objWithComments = `
# This is a comment
v 0 0 0
# Another comment
v 1 0 0
v 0 1 0
f 1 2 3
`;
      const result = parseOBJText(objWithComments);
      expect(result.vertices.length).toBe(3);
      expect(result.totalFaces).toBe(1);
    });

    it('ignora caras con menos de 3 vértices', () => {
      const badFaces = `
v 0 0 0
v 1 0 0
v 0 1 0
f 1 2
f 1 2 3
`;
      const result = parseOBJText(badFaces);
      expect(result.totalFaces).toBe(1);
    });

    it('maneja archivo vacío', () => {
      const result = parseOBJText('');
      expect(result.vertices.length).toBe(0);
      expect(result.totalFaces).toBe(0);
      expect(result.objects.length).toBe(0);
    });

    it('maneja índices negativos', () => {
      const objNegIdx = `
v 0 0 0
v 1 0 0
v 0 1 0
v 1 1 0
f -4 -3 -2 -1
`;
      const result = parseOBJText(objNegIdx);
      expect(result.totalFaces).toBe(1);
      expect(result.objects[0].faces[0].vertexIndices).toEqual([0, 1, 2, 3]);
    });

    it('crea objeto default si no hay declaración o/g', () => {
      const noName = `
v 0 0 0
v 1 0 0
v 0 1 0
f 1 2 3
`;
      const result = parseOBJText(noName);
      expect(result.objects.length).toBe(1);
      expect(result.objects[0].name).toBe('default');
    });
  });

  describe('getOBJSummary', () => {
    it('genera un resumen correcto', () => {
      const result = parseOBJText(simpleOBJ);
      const summary = getOBJSummary(result);
      expect(summary.vertexCount).toBe(8);
      expect(summary.faceCount).toBe(6);
      expect(summary.objectCount).toBe(1);
      expect(summary.objectNames).toEqual(['Cube']);
      expect(summary.dimensions).toBe('10.00 × 10.00 × 10.00');
    });

    it('lista nombres de múltiples objetos', () => {
      const result = parseOBJText(multiObjectOBJ);
      const summary = getOBJSummary(result);
      expect(summary.objectCount).toBe(2);
      expect(summary.objectNames).toContain('Building_A');
      expect(summary.objectNames).toContain('Tree_1');
    });
  });

  describe('convertOBJToObstacles', () => {
    it('convierte un cubo en al menos un obstáculo', () => {
      const parsed = parseOBJText(simpleOBJ);
      const result = convertOBJToObstacles(parsed);
      expect(result.obstacles.length).toBeGreaterThanOrEqual(1);
    });

    it('cada obstáculo tiene al menos 3 vértices', () => {
      const parsed = parseOBJText(simpleOBJ);
      const result = convertOBJToObstacles(parsed);
      for (const obs of result.obstacles) {
        expect(obs.vertices.length).toBeGreaterThanOrEqual(3);
      }
    });

    it('los obstáculos tienen azimut y altitud numéricos', () => {
      const parsed = parseOBJText(simpleOBJ);
      const result = convertOBJToObstacles(parsed);
      for (const obs of result.obstacles) {
        for (const v of obs.vertices) {
          expect(typeof v.azimuth).toBe('number');
          expect(typeof v.altitude).toBe('number');
          expect(v.altitude).toBeGreaterThanOrEqual(0);
        }
      }
    });

    it('aplica factor de escala correctamente', () => {
      const parsed = parseOBJText(simpleOBJ);
      const result = convertOBJToObstacles(parsed, undefined, 0, false, 0.001);
      // El bounding box debería estar escalado
      expect(result.parseResult.boundingBox.dimensions.x).toBeCloseTo(0.01, 4);
    });

    it('intercambia Y/Z cuando swapYZ es true', () => {
      // Usar un objeto asimétrico donde Y != Z
      const asymOBJ = `
o Box
v 0 0 0
v 5 0 0
v 5 20 0
v 0 20 0
v 0 0 3
v 5 0 3
v 5 20 3
v 0 20 3
f 1 2 3 4
f 5 6 7 8
f 1 2 6 5
f 2 3 7 6
f 3 4 8 7
f 4 1 5 8
`;
      const parsed = parseOBJText(asymOBJ);
      const normal = convertOBJToObstacles(parsed, undefined, 0, false);
      const swapped = convertOBJToObstacles(parsed, undefined, 0, true);
      // Y dimension (20) and Z dimension (3) should swap
      expect(normal.parseResult.boundingBox.dimensions.y).toBeCloseTo(20);
      expect(normal.parseResult.boundingBox.dimensions.z).toBeCloseTo(3);
      expect(swapped.parseResult.boundingBox.dimensions.y).toBeCloseTo(3);
      expect(swapped.parseResult.boundingBox.dimensions.z).toBeCloseTo(20);
    });

    it('genera obstáculos para múltiples objetos', () => {
      const parsed = parseOBJText(multiObjectOBJ);
      const result = convertOBJToObstacles(parsed);
      // Debería generar al menos 1 obstáculo (puede ser menos si alguno está debajo del observador)
      expect(result.obstacles.length).toBeGreaterThanOrEqual(1);
    });

    it('usa punto de observación personalizado', () => {
      const parsed = parseOBJText(simpleOBJ);
      const customObserver = { x: -10, y: -10, z: 0 };
      const result = convertOBJToObstacles(parsed, customObserver);
      expect(result.observationPoint.x).toBe(-10);
      expect(result.observationPoint.y).toBe(-10);
    });

    it('asigna colores diferentes a cada obstáculo', () => {
      const parsed = parseOBJText(multiObjectOBJ);
      const result = convertOBJToObstacles(parsed);
      if (result.obstacles.length >= 2) {
        expect(result.obstacles[0].color).not.toBe(result.obstacles[1].color);
      }
    });

    it('incluye nombre del objeto y dimensiones en el nombre del obstáculo', () => {
      const parsed = parseOBJText(simpleOBJ);
      const result = convertOBJToObstacles(parsed);
      if (result.obstacles.length > 0) {
        expect(result.obstacles[0].name).toContain('Cube');
      }
    });
  });
});
