/**
 * Interfaz puente entre el Simulador BIPV IAM+Soiling y el Simulador de Energía.
 * 
 * Permite enviar resultados del análisis IAM+Soiling al Simulador de Producción
 * para integrarlos como datos de referencia y pre-llenar parámetros del sistema.
 */

export interface BIPVToEnergyData {
  /** Producción mensual calculada por IAM+Soiling (kWh) - 12 valores */
  produccionMensualKwh: number[];
  /** Eficiencia ajustada final (0-1) después de todas las pérdidas */
  eficienciaAjustada: number;
  /** Potencia pico del sistema (W) */
  potenciaPicoW: number;
  /** Inclinación de la fachada (grados) */
  tilt: number;
  /** Azimut de la fachada (grados) */
  azimuth: number;
  /** Área total de vidrio BIPV (m²) */
  areaM2: number;
  /** Nivel de transparencia del vidrio (0-1) */
  transparencia: number;
  /** Nombre de la tecnología de vidrio */
  technology: string;
  /** Generación de la tecnología (1G/2G/3G) */
  generation: string;
  /** Factor IAM promedio anual */
  iamPromedio: number;
  /** Factor de soiling promedio anual */
  soilingPromedio: number;
  /** Factor térmico promedio anual */
  factorTermicoPromedio: number;
  /** Energía anual total (kWh) */
  energiaAnualKwh: number;
  /** Energía anual por m² (kWh/m²) */
  energiaAnualKwhM2: number;
  /** Modelo de transposición usado */
  transpositionModel: 'isotropic' | 'perez';
  /** Coeficiente de temperatura (%/°C) de la tecnología BIPV */
  coefTemperatura: number;
  /** NOCT de la tecnología BIPV (°C) */
  noct: number;
  /** Factor k_bipv del montaje térmico */
  kBipv: number;
  /** Nombre de la superficie/fachada del modelo 3D */
  surfaceName?: string;
  /** ID del panel seleccionado en IAM+Soiling BIPV (del catálogo PanelTechnology) */
  panelId?: string;
  /** Potencia nominal del panel individual (W) - para sincronizar con el selector del Simulador */
  panelPmax?: number;
  /** Eficiencia STC del panel (%) */
  panelEfficiencySTC?: number;
  /** Dimensiones del panel (mm) */
  panelLengthMm?: number;
  panelWidthMm?: number;
  /** IAM mensual variable (12 valores, factor de retención 0-1 por mes) */
  iamMensual?: number[];
  /** Soiling mensual variable (12 valores, pérdida fraccional 0-1 por mes) */
  soilingMensual?: number[];
}
