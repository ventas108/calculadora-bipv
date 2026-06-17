/**
 * Catálogo de Tecnologías de Vidrios Fotovoltaicos BIPV
 * 
 * Tres generaciones de vidrios con parámetros de reflexión geométrica (b0_ashrae),
 * eficiencia base, coeficientes térmicos y NOCT.
 * 
 * Fuente: Configuración del Orquestador BIPV (site_designer.json)
 */

import type { BIPVGlassTechnology, SoilingConfig } from './iamSoilingEngine';

// ─── Catálogo de Tecnologías ────────────────────────────────────────────────

export const BIPV_GLASS_CATALOG: BIPVGlassTechnology[] = [
  {
    id: '1G_Silicio_Amorfo',
    name: 'Silicio Amorfo (a-Si)',
    generation: '1G',
    generationLabel: '1ª Generación / Capa Fina Estándar',
    eficienciaBase: 0.10,
    coefTemperatura: -0.0020,
    noct: 45,
    b0Ashrae: 0.05,
    description: 'Tecnología madura de capa fina con buena respuesta a luz difusa. Menor eficiencia pero mejor comportamiento con ángulos altos de incidencia y temperaturas elevadas.',
  },
  {
    id: '2G_CdTe',
    name: 'Teluro de Cadmio (CdTe)',
    generation: '2G',
    generationLabel: '2ª Generación / Teluro de Cadmio Avanzado',
    eficienciaBase: 0.16,
    coefTemperatura: -0.0025,
    noct: 45,
    b0Ashrae: 0.045,
    description: 'Tecnología avanzada de capa fina con mejor eficiencia. Menor coeficiente de reflexión (b0=0.045) permite captar más luz en ángulos oblicuos. Sensible a temperatura.',
  },
  {
    id: '3G_Perovskita',
    name: 'Perovskita',
    generation: '3G',
    generationLabel: '3ª Generación / Células Emergentes',
    eficienciaBase: 0.20,
    coefTemperatura: -0.0015,
    noct: 42,
    b0Ashrae: 0.06,
    description: 'Tecnología emergente de alta eficiencia con excelente coeficiente de temperatura. Mayor reflexión geométrica (b0=0.06) por textura superficial, pero compensada por alta eficiencia base.',
  },
  // ===== HIITIO CdTe Semitransparente (H12-H15) =====
  {
    id: 'HIITIO_H12_CdTe_0T',
    name: 'HIITIO H12 · CdTe 0% T (115W)',
    generation: '2G',
    generationLabel: '2ª Generación / HIITIO CdTe Opaco',
    eficienciaBase: 0.1597,
    coefTemperatura: -0.0029,
    noct: 46,
    b0Ashrae: 0.045,
    description: 'HIITIO H12: CdTe opaco 115W. Lucernarios opacos, cubiertas semicerradas. Voc 125.5V.',
  },
  {
    id: 'HIITIO_H13_CdTe_20T',
    name: 'HIITIO H13 · CdTe 20% T (92W)',
    generation: '2G',
    generationLabel: '2ª Generación / HIITIO CdTe 20% Transp.',
    eficienciaBase: 0.1278,
    coefTemperatura: -0.0029,
    noct: 46,
    b0Ashrae: 0.045,
    description: 'HIITIO H13: CdTe semitransparente 20%, 92W. Fachada con visión exterior.',
  },
  {
    id: 'HIITIO_H14_CdTe_40T',
    name: 'HIITIO H14 · CdTe 40% T (69W)',
    generation: '2G',
    generationLabel: '2ª Generación / HIITIO CdTe 40% Transp.',
    eficienciaBase: 0.0958,
    coefTemperatura: -0.0029,
    noct: 46,
    b0Ashrae: 0.045,
    description: 'HIITIO H14: CdTe semitransparente 40%, 69W. Balance generación-luz natural.',
  },
  {
    id: 'HIITIO_H15_CdTe_60T',
    name: 'HIITIO H15 · CdTe 60% T (46W)',
    generation: '2G',
    generationLabel: '2ª Generación / HIITIO CdTe 60% Transp.',
    eficienciaBase: 0.0639,
    coefTemperatura: -0.0029,
    noct: 46,
    b0Ashrae: 0.045,
    description: 'HIITIO H15: CdTe alta transparencia 60%, 46W. Vidrio solar arquitectónico con máxima visibilidad.',
  },
  // ===== EINNOVA Vidrio FV (P18) =====
  {
    id: 'EINNOVA_P18_Vidrio_40T',
    name: 'EINNOVA P18 · Vidrio FV 40% T (58W)',
    generation: '2G',
    generationLabel: '2ª Generación / EINNOVA Vidrio FV',
    eficienciaBase: 0.070,
    coefTemperatura: -0.00214,
    noct: 46,
    b0Ashrae: 0.045,
    description: 'EINNOVA P18: 58W vidrio FV 40% transparencia. Claraboyas, fachadas curtain wall LEED/EDGE.',
  },
];

// ─── Niveles de Transparencia ───────────────────────────────────────────────

export interface TransparencyLevel {
  value: number;
  label: string;
  description: string;
}

export const TRANSPARENCY_LEVELS: TransparencyLevel[] = [
  { value: 0.0, label: '0% (Opaco)', description: 'Totalmente opaco - Máxima generación eléctrica (ej: tejas, fachada opaca, revestimiento)' },
  { value: 0.10, label: '10%', description: 'Mínima transparencia - Máxima generación eléctrica' },
  { value: 0.20, label: '20%', description: 'Baja transparencia - Alta generación con algo de luz natural' },
  { value: 0.30, label: '30%', description: 'Transparencia moderada-baja - Balance generación/iluminación' },
  { value: 0.40, label: '40%', description: 'Transparencia media - Balance equilibrado' },
  { value: 0.50, label: '50%', description: 'Transparencia media-alta - Prioriza iluminación natural' },
  { value: 0.60, label: '60%', description: 'Alta transparencia - Máxima luz natural, menor generación' },
];

// ─── Configuraciones de Soiling por Zona Climática ──────────────────────────

export interface SoilingPreset {
  id: string;
  name: string;
  description: string;
  config: SoilingConfig;
}

export const SOILING_PRESETS: SoilingPreset[] = [
  {
    id: 'tropical_urbano',
    name: 'Tropical Urbano',
    description: 'Clima tropical con contaminación urbana moderada. Lluvias frecuentes ayudan al autolavado.',
    config: {
      monthlyFactors: {
        1: 0.05, 2: 0.06, 3: 0.04, 4: 0.02, 5: 0.02, 6: 0.04,
        7: 0.05, 8: 0.06, 9: 0.04, 10: 0.02, 11: 0.01, 12: 0.04,
      },
      precipitableWaterThreshold: 25.0,
      autoWashReduction: 0.15,
    },
  },
  {
    id: 'arido_industrial',
    name: 'Árido Industrial',
    description: 'Clima seco con alta contaminación industrial. Poca lluvia, acumulación significativa de polvo.',
    config: {
      monthlyFactors: {
        1: 0.08, 2: 0.09, 3: 0.10, 4: 0.11, 5: 0.12, 6: 0.13,
        7: 0.14, 8: 0.13, 9: 0.11, 10: 0.09, 11: 0.08, 12: 0.07,
      },
      precipitableWaterThreshold: 30.0,
      autoWashReduction: 0.20,
    },
  },
  {
    id: 'templado_limpio',
    name: 'Templado Limpio',
    description: 'Clima templado con baja contaminación. Lluvias regulares mantienen los paneles limpios.',
    config: {
      monthlyFactors: {
        1: 0.02, 2: 0.02, 3: 0.03, 4: 0.03, 5: 0.02, 6: 0.02,
        7: 0.03, 8: 0.03, 9: 0.02, 10: 0.02, 11: 0.01, 12: 0.01,
      },
      precipitableWaterThreshold: 20.0,
      autoWashReduction: 0.10,
    },
  },
  {
    id: 'costero_salino',
    name: 'Costero Salino',
    description: 'Ambiente costero con depósitos de sal marina. Requiere limpieza frecuente.',
    config: {
      monthlyFactors: {
        1: 0.06, 2: 0.07, 3: 0.07, 4: 0.06, 5: 0.05, 6: 0.05,
        7: 0.06, 8: 0.07, 9: 0.07, 10: 0.06, 11: 0.05, 12: 0.05,
      },
      precipitableWaterThreshold: 22.0,
      autoWashReduction: 0.25,
    },
  },
  {
    id: 'personalizado',
    name: 'Personalizado',
    description: 'Configuración manual de factores de suciedad mensuales.',
    config: {
      monthlyFactors: {
        1: 0.05, 2: 0.05, 3: 0.05, 4: 0.05, 5: 0.05, 6: 0.05,
        7: 0.05, 8: 0.05, 9: 0.05, 10: 0.05, 11: 0.05, 12: 0.05,
      },
      precipitableWaterThreshold: 25.0,
      autoWashReduction: 0.15,
    },
  },
];

// ─── Factores k_bipv de Confinamiento Térmico ───────────────────────────────

export interface ThermalMountingType {
  id: string;
  name: string;
  kBipv: number;
  description: string;
}

export const THERMAL_MOUNTING_TYPES: ThermalMountingType[] = [
  {
    id: 'ventilado_libre',
    name: 'Montaje Ventilado Libre',
    kBipv: 1.0,
    description: 'Panel con ventilación libre por ambas caras (rack abierto). Mejor disipación térmica.',
  },
  {
    id: 'semi_ventilado',
    name: 'Semi-Ventilado',
    kBipv: 1.15,
    description: 'Ventilación parcial por la parte posterior. Típico de fachadas con cámara de aire.',
  },
  {
    id: 'fachada_confinada',
    name: 'Fachada Confinada (BIPV)',
    kBipv: 1.3,
    description: 'Integrado en fachada con ventilación limitada. Caso típico de vidrio BIPV en muro cortina.',
  },
  {
    id: 'sin_ventilacion',
    name: 'Sin Ventilación',
    kBipv: 1.5,
    description: 'Completamente integrado sin cámara de aire. Mayor temperatura de celda.',
  },
];

// ─── Helpers ────────────────────────────────────────────────────────────────

export function getTechnologyById(id: string): BIPVGlassTechnology | undefined {
  return BIPV_GLASS_CATALOG.find(t => t.id === id);
}

export function getTechnologiesByGeneration(gen: '1G' | '2G' | '3G'): BIPVGlassTechnology[] {
  return BIPV_GLASS_CATALOG.filter(t => t.generation === gen);
}

export function getSoilingPresetById(id: string): SoilingPreset | undefined {
  return SOILING_PRESETS.find(p => p.id === id);
}

export function getMountingTypeById(id: string): ThermalMountingType | undefined {
  return THERMAL_MOUNTING_TYPES.find(m => m.id === id);
}
