/**
 * Configuraciones predefinidas de instalación BIPV
 * 
 * Cada configuración define:
 * - Inclinación típica del montaje
 * - Pérdidas específicas del sistema según tipo de instalación
 * - Costos de estructura y mano de obra por panel
 * - Factor de separación recomendado
 * - Descripción técnica y notas
 */

export interface InstallationConfig {
  id: string;
  name: string;
  description: string;
  icon: string; // emoji para selector visual
  
  // Parámetros de orientación
  defaultTilt: number;         // Inclinación por defecto (°)
  tiltRange: [number, number]; // Rango permitido de inclinación
  defaultAzimuth: number;      // Azimut por defecto (° desde norte, 180=sur)
  azimuthLocked: boolean;      // Si el azimut está fijo (ej: fachada)
  
  // Pérdidas específicas del tipo de instalación
  losses: {
    soiling: number;           // Suciedad (%) - varía según inclinación
    mismatch: number;          // Desajuste (%) - mayor en BIPV integrado
    dcWiring: number;          // Cableado DC (%) - mayor en fachadas por distancia
    acWiring: number;          // Cableado AC (%)
    inverterEfficiency: number; // Eficiencia inversor (%)
    transformerLosses: number; // Transformador (%)
    availabilityLosses: number; // Disponibilidad (%)
  };
  
  // Costos de estructura y montaje
  structureCostPerPanel: number;  // USD por panel - estructura
  laborCostPerPanel: number;      // USD por panel - mano de obra
  
  // Factor de separación recomendado
  recommendedSpacing: number;     // Factor multiplicador (1.0 = sin separación)
  
  // Montaje PVGIS
  pvgisMountingPlace: 'free' | 'building';
  
  // Notas técnicas
  notes: string[];
}

export const INSTALLATION_CONFIGS: InstallationConfig[] = [
  {
    id: 'rooftop_tilted',
    name: 'Cubierta Inclinada',
    description: 'Paneles montados sobre cubierta existente con inclinación fija. Configuración más común para edificios residenciales y comerciales.',
    icon: '🏠',
    defaultTilt: 15,
    tiltRange: [5, 45],
    defaultAzimuth: 180,
    azimuthLocked: false,
    losses: {
      soiling: 2.5,
      mismatch: 1.5,
      dcWiring: 2.0,
      acWiring: 1.5,
      inverterEfficiency: 97,
      transformerLosses: 0.5,
      availabilityLosses: 1.0,
    },
    structureCostPerPanel: 25,
    laborCostPerPanel: 35,
    recommendedSpacing: 1.15,
    pvgisMountingPlace: 'building',
    notes: [
      'Inclinación típica: 10-20° en zonas tropicales, 25-35° en latitudes medias',
      'Ventilación natural por convección bajo los paneles',
      'Acceso relativamente fácil para mantenimiento',
    ],
  },
  {
    id: 'rooftop_flat',
    name: 'Cubierta Plana',
    description: 'Paneles sobre estructura elevada en azotea plana. Permite optimizar inclinación y orientación libremente.',
    icon: '🏢',
    defaultTilt: 10,
    tiltRange: [0, 35],
    defaultAzimuth: 180,
    azimuthLocked: false,
    losses: {
      soiling: 3.0,
      mismatch: 1.5,
      dcWiring: 2.0,
      acWiring: 1.5,
      inverterEfficiency: 97,
      transformerLosses: 0.5,
      availabilityLosses: 1.0,
    },
    structureCostPerPanel: 35,
    laborCostPerPanel: 40,
    recommendedSpacing: 1.35,
    pvgisMountingPlace: 'free',
    notes: [
      'Requiere estructura de soporte con lastre o anclaje',
      'Mayor separación entre filas para evitar sombreado mutuo',
      'Ideal para grandes superficies comerciales e industriales',
    ],
  },
  {
    id: 'facade_vertical',
    name: 'Fachada Vertical',
    description: 'Paneles BIPV integrados en fachada vertical del edificio. Menor producción pero alta visibilidad arquitectónica.',
    icon: '🏗️',
    defaultTilt: 90,
    tiltRange: [75, 90],
    defaultAzimuth: 180,
    azimuthLocked: true,
    losses: {
      soiling: 1.5,
      mismatch: 3.0,
      dcWiring: 3.0,
      acWiring: 2.0,
      inverterEfficiency: 96.5,
      transformerLosses: 0.5,
      availabilityLosses: 1.5,
    },
    structureCostPerPanel: 55,
    laborCostPerPanel: 65,
    recommendedSpacing: 1.05,
    pvgisMountingPlace: 'building',
    notes: [
      'Producción ~40-60% menor que instalación óptima en cubierta',
      'Auto-limpieza por lluvia reduce suciedad',
      'Cableado más largo por recorrido vertical',
      'Mayor desajuste por sombreado parcial de edificios adyacentes',
      'Ideal para paneles CdTe semitransparentes y HJT Curtain Wall',
    ],
  },
  {
    id: 'facade_inclined',
    name: 'Fachada Inclinada',
    description: 'Paneles BIPV en fachada con inclinación (45-75°). Compromiso entre integración arquitectónica y producción energética.',
    icon: '📐',
    defaultTilt: 60,
    tiltRange: [45, 75],
    defaultAzimuth: 180,
    azimuthLocked: true,
    losses: {
      soiling: 2.0,
      mismatch: 2.5,
      dcWiring: 2.5,
      acWiring: 1.5,
      inverterEfficiency: 97,
      transformerLosses: 0.5,
      availabilityLosses: 1.0,
    },
    structureCostPerPanel: 50,
    laborCostPerPanel: 55,
    recommendedSpacing: 1.08,
    pvgisMountingPlace: 'building',
    notes: [
      'Producción ~70-85% respecto a inclinación óptima',
      'Buen compromiso entre estética y rendimiento',
      'Aplicable a fachadas ventiladas y muro cortina inclinado',
    ],
  },
  {
    id: 'pergola',
    name: 'Pérgola Solar',
    description: 'Estructura de pérgola con paneles como cubierta. Doble función: generación eléctrica y sombra para espacios exteriores.',
    icon: '🌿',
    defaultTilt: 8,
    tiltRange: [0, 20],
    defaultAzimuth: 180,
    azimuthLocked: false,
    losses: {
      soiling: 3.5,
      mismatch: 2.0,
      dcWiring: 2.0,
      acWiring: 1.5,
      inverterEfficiency: 97,
      transformerLosses: 0.5,
      availabilityLosses: 1.0,
    },
    structureCostPerPanel: 60,
    laborCostPerPanel: 50,
    recommendedSpacing: 1.1,
    pvgisMountingPlace: 'free',
    notes: [
      'Estructura independiente con pilares y vigas',
      'Paneles semitransparentes permiten paso parcial de luz',
      'Mayor acumulación de suciedad por baja inclinación',
      'Ideal para estacionamientos, terrazas y áreas de descanso',
    ],
  },
  {
    id: 'canopy',
    name: 'Marquesina / Carport',
    description: 'Estructura tipo marquesina para estacionamientos o accesos. Alta visibilidad y protección contra lluvia/sol.',
    icon: '🅿️',
    defaultTilt: 5,
    tiltRange: [0, 15],
    defaultAzimuth: 180,
    azimuthLocked: false,
    losses: {
      soiling: 4.0,
      mismatch: 2.0,
      dcWiring: 2.5,
      acWiring: 2.0,
      inverterEfficiency: 97,
      transformerLosses: 0.5,
      availabilityLosses: 1.0,
    },
    structureCostPerPanel: 75,
    laborCostPerPanel: 55,
    recommendedSpacing: 1.08,
    pvgisMountingPlace: 'free',
    notes: [
      'Estructura metálica robusta (acero galvanizado o aluminio)',
      'Costo de estructura más alto por requisitos estructurales',
      'Mayor suciedad por baja inclinación y exposición a polvo vehicular',
      'Ideal para estacionamientos comerciales y corporativos',
      'Posibilidad de integrar carga de vehículos eléctricos',
    ],
  },
  {
    id: 'bipv_imported',
    name: 'BIPV (Importado)',
    description: 'Configuración importada del Optimizador BIPV IAM+Soiling. Ángulos definidos por el modelo 3D del edificio. No editar manualmente.',
    icon: '🔬',
    defaultTilt: 20,
    tiltRange: [0, 90],
    defaultAzimuth: 180,
    azimuthLocked: false,
    losses: {
      soiling: 2.0,
      mismatch: 2.0,
      dcWiring: 2.0,
      acWiring: 1.5,
      inverterEfficiency: 97,
      transformerLosses: 0.5,
      availabilityLosses: 1.0,
    },
    structureCostPerPanel: 45,
    laborCostPerPanel: 50,
    recommendedSpacing: 1.0,
    pvgisMountingPlace: 'building',
    notes: [
      'Ángulos de inclinación y azimut definidos por el modelo 3D importado',
      'Configuración sincronizada desde el Optimizador IAM+Soiling BIPV',
      'Las pérdidas se ajustan según la tecnología BIPV seleccionada',
      'No modificar ángulos manualmente — usar "Volver al BIPV" para recalcular',
      'Factor de separación 1.0 (integrado en envolvente, sin separación entre filas)',
    ],
  },
];

/**
 * Obtener configuración por ID
 */
export function getInstallationConfig(id: string): InstallationConfig | undefined {
  return INSTALLATION_CONFIGS.find(c => c.id === id);
}

/**
 * Obtener la configuración por defecto (cubierta inclinada)
 */
export function getDefaultInstallationConfig(): InstallationConfig {
  return INSTALLATION_CONFIGS[0];
}

/**
 * Calcular factor de reducción de producción estimado respecto a inclinación óptima
 * Basado en modelo simplificado cos(tilt - optimalTilt)
 */
export function estimateProductionFactor(tilt: number, latitude: number): number {
  const optimalTilt = Math.abs(latitude);
  const diff = Math.abs(tilt - optimalTilt);
  // Factor coseno suavizado: 1.0 en óptimo, ~0.5 a 90° de diferencia
  return Math.max(0.3, Math.cos(diff * Math.PI / 180));
}
