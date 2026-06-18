/**
 * Panel Technology Templates
 * 
 * Incluye los 17 productos BIPV del catálogo HIITIO Colombia,
 * los 18 productos BIPV del catálogo EINNOVA Colombia,
 * y tecnologías genéricas de referencia.
 * 
 * Fuentes: Catálogo HIITIO 2024, Catálogo EINNOVA 2024, PVGIS v5.3, IEA-PVPS, Atlas IDEAM/UPME
 */

export type PanelCategory =
  | 'topcon_flex' | 'hjt_curtain' | 'hjt_tile' | 'cdte_semit' | 'cdte_bipv' | 'cigs'
  | 'einnova_antirreflejo' | 'einnova_bifacial' | 'einnova_teja_bc' | 'einnova_teja_plana'
  | 'einnova_color_panel' | 'einnova_fachada' | 'einnova_flexible' | 'einnova_agripv'
  | 'einnova_pavimento' | 'einnova_vidrio'
  | 'soltech_dvh' | 'soltech_laminado' | 'soltech_opaco' | 'soltech_st' | 'soltech_teja' | 'soltech_ncl'
  | 'generic';

export type PanelBrand = 'hiitio' | 'einnova' | 'soltech' | 'generic';

/** Compatibilidad regional: 3=óptimo, 2=aceptable, 1=no recomendado */
export interface RegionalCompatibility {
  caribe: 1 | 2 | 3;
  andina: 1 | 2 | 3;
  pacifica: 1 | 2 | 3;
  orinoquia: 1 | 2 | 3;
  amazonia: 1 | 2 | 3;
  insular: 1 | 2 | 3;
  notes: string;
}

export interface PanelTechnology {
  id: string;
  name: string;
  category: PanelCategory;
  brand: PanelBrand;
  description: string;
  // Parámetros eléctricos STC
  pmax: number;                   // Potencia máxima (W)
  voc: number;                    // Voltaje circuito abierto (V)
  isc: number;                    // Corriente cortocircuito (A)
  vmp: number;                    // Voltaje punto máx. potencia (V)
  imp: number;                    // Corriente punto máx. potencia (A)
  efficiencySTC: number;          // Eficiencia en STC (%)
  tempCoeffPmax: number;          // Coef. temperatura Pmax (%/°C)
  // Dimensiones y peso
  lengthMm: number;               // Largo (mm)
  widthMm: number;                // Ancho (mm)
  weightKg: number;               // Peso (kg)
  // Parámetros térmicos y de sistema
  noct: number;                   // NOCT (°C) - estimado según tipo montaje
  systemLoss: number;             // Pérdidas del sistema por defecto (%)
  degradationAnnual: number;      // Degradación anual (%)
  // PVGIS mapping
  pvgisTechchoice: string;        // crystSi, CdTe, CIS, Unknown
  pvgisMountingplace: 'free' | 'building'; // free=rack, building=BIPV
  // Precio de referencia
  priceUSD: number;               // Precio unitario de referencia (USD/panel)
  pricePerWp: number;             // Precio por Wp (USD/Wp) - referencia
  // Aplicación
  application: string;            // Uso BIPV recomendado
  isCustom: boolean;
  color: string;
  hiitioId: string;               // ID catálogo HIITIO (H01-H17) o EINNOVA (P01-P18) o ''
  regionalCompatibility?: RegionalCompatibility; // Diagnóstico por región (solo EINNOVA)
}

/**
 * 17 Productos BIPV HIITIO + tecnologías genéricas de referencia
 */
export const DEFAULT_PANEL_TECHNOLOGIES: PanelTechnology[] = [
  // ===== TOPCon Flex (H01-H05) =====
  {
    id: 'H01', hiitioId: 'H01', name: 'H01 · TOPCon Flex HCFM-580',
    category: 'topcon_flex',
    description: 'N-TOPCon flexible 580W. Máxima potencia, ultradelgado 2.7mm, 3 kg/m². Cubiertas curvas e irregulares.',
    pmax: 580, voc: 53.03, isc: 13.86, vmp: 44.19, imp: 13.13,
    efficiencySTC: 23.5, tempCoeffPmax: -0.26,
    lengthMm: 2260, widthMm: 1219, weightKg: 8.5,
    noct: 43, systemLoss: 14, degradationAnnual: 0.40,
    pvgisTechchoice: 'crystSi', pvgisMountingplace: 'free',
    application: 'Cubiertas curvas e irregulares; baja capacidad portante; máxima potencia',
    priceUSD: 290, pricePerWp: 0.50,
    isCustom: false, color: '#2563eb', brand: 'hiitio',
    regionalCompatibility: { caribe: 3, andina: 1, pacifica: 3, orinoquia: 3, amazonia: 3, insular: 3, notes: '23.5% eficiencia, 3 kg/m², coef -0.26%/°C; el todoterreno' },
  },
  {
    id: 'H02', hiitioId: 'H02', name: 'H02 · TOPCon Flex HCFM-570',
    category: 'topcon_flex',
    description: 'N-TOPCon flexible 570W. Cubiertas curvas, vehículos y barcos.',
    pmax: 570, voc: 52.77, isc: 13.78, vmp: 43.68, imp: 13.05,
    efficiencySTC: 23.5, tempCoeffPmax: -0.26,
    lengthMm: 2260, widthMm: 1219, weightKg: 8.5,
    noct: 43, systemLoss: 14, degradationAnnual: 0.40,
    pvgisTechchoice: 'crystSi', pvgisMountingplace: 'free',
    application: 'Cubiertas curvas; vehículos y barcos; integración limpia sin marco',
    priceUSD: 285, pricePerWp: 0.50,
    isCustom: false, color: '#3b82f6', brand: 'hiitio',
    regionalCompatibility: { caribe: 3, andina: 1, pacifica: 3, orinoquia: 3, amazonia: 3, insular: 3, notes: '23.5% eficiencia, 3 kg/m², coef -0.26%/°C; el todoterreno' },
  },
  {
    id: 'H03', hiitioId: 'H03', name: 'H03 · TOPCon Flex HCFM-560',
    category: 'topcon_flex',
    description: 'N-TOPCon flexible 560W. Cubiertas industriales metálicas existentes.',
    pmax: 560, voc: 52.58, isc: 13.69, vmp: 43.18, imp: 12.97,
    efficiencySTC: 23.5, tempCoeffPmax: -0.26,
    lengthMm: 2260, widthMm: 1219, weightKg: 8.5,
    noct: 43, systemLoss: 14, degradationAnnual: 0.40,
    pvgisTechchoice: 'crystSi', pvgisMountingplace: 'free',
    application: 'Cubiertas industriales metálicas existentes',
    priceUSD: 280, pricePerWp: 0.50,
    isCustom: false, color: '#60a5fa', brand: 'hiitio',
    regionalCompatibility: { caribe: 3, andina: 1, pacifica: 3, orinoquia: 3, amazonia: 3, insular: 3, notes: '23.5% eficiencia, 3 kg/m², coef -0.26%/°C; el todoterreno' },
  },
  {
    id: 'H04', hiitioId: 'H04', name: 'H04 · TOPCon Flex HCFM-550',
    category: 'topcon_flex',
    description: 'N-TOPCon flexible 550W. Cubiertas con limitación de carga estructural.',
    pmax: 550, voc: 52.32, isc: 13.65, vmp: 42.63, imp: 12.91,
    efficiencySTC: 23.5, tempCoeffPmax: -0.26,
    lengthMm: 2260, widthMm: 1219, weightKg: 8.5,
    noct: 43, systemLoss: 14, degradationAnnual: 0.40,
    pvgisTechchoice: 'crystSi', pvgisMountingplace: 'free',
    application: 'Cubiertas con limitación de carga estructural',
    priceUSD: 275, pricePerWp: 0.50,
    isCustom: false, color: '#93c5fd', brand: 'hiitio',
    regionalCompatibility: { caribe: 3, andina: 1, pacifica: 3, orinoquia: 3, amazonia: 3, insular: 3, notes: '23.5% eficiencia, 3 kg/m², coef -0.26%/°C; el todoterreno' },
  },
  {
    id: 'H05', hiitioId: 'H05', name: 'H05 · TOPCon Flex HCFM-540',
    category: 'topcon_flex',
    description: 'N-TOPCon flexible 540W. Cubiertas residenciales y comerciales con baja portancia.',
    pmax: 540, voc: 51.98, isc: 13.58, vmp: 42.23, imp: 12.79,
    efficiencySTC: 23.5, tempCoeffPmax: -0.26,
    lengthMm: 2260, widthMm: 1219, weightKg: 8.5,
    noct: 43, systemLoss: 14, degradationAnnual: 0.40,
    pvgisTechchoice: 'crystSi', pvgisMountingplace: 'free',
    application: 'Cubiertas residenciales y comerciales con baja portancia',
    priceUSD: 270, pricePerWp: 0.50,
    isCustom: false, color: '#bfdbfe', brand: 'hiitio',
    regionalCompatibility: { caribe: 3, andina: 1, pacifica: 3, orinoquia: 3, amazonia: 3, insular: 3, notes: '23.5% eficiencia, 3 kg/m², coef -0.26%/°C; el todoterreno' },
  },

  // ===== HJT Curtain Wall (H06-H08) =====
  {
    id: 'H06', hiitioId: 'H06', name: 'H06 · HJT Curtain Wall 395W',
    category: 'hjt_curtain',
    description: 'HJT Curtain Wall 395W. Muros cortina/fachada vidriada de edificios oficinas. Carga frontal 5400 Pa.',
    pmax: 395, voc: 29.94, isc: 16.27, vmp: 25.75, imp: 15.34,
    efficiencySTC: 19.0, tempCoeffPmax: -0.26,
    lengthMm: 1805, widthMm: 1150, weightKg: 67.5,
    noct: 48, systemLoss: 18, degradationAnnual: 0.40,
    pvgisTechchoice: 'crystSi', pvgisMountingplace: 'building',
    application: 'Muros cortina / Fachada vidriada de edificios oficinas',
    priceUSD: 520, pricePerWp: 1.32,
    isCustom: false, color: '#7c3aed', brand: 'hiitio',
    regionalCompatibility: { caribe: 3, andina: 3, pacifica: 2, orinoquia: 3, amazonia: 1, insular: 3, notes: 'Fachadas vidriadas premium; 5400 Pa carga frontal' },
  },
  {
    id: 'H07', hiitioId: 'H07', name: 'H07 · HJT Curtain Wall 390W',
    category: 'hjt_curtain',
    description: 'HJT Curtain Wall 390W. Fachada ventilada edificios corporativos.',
    pmax: 390, voc: 29.79, isc: 16.21, vmp: 25.51, imp: 15.29,
    efficiencySTC: 18.8, tempCoeffPmax: -0.26,
    lengthMm: 1805, widthMm: 1150, weightKg: 67.5,
    noct: 48, systemLoss: 18, degradationAnnual: 0.40,
    pvgisTechchoice: 'crystSi', pvgisMountingplace: 'building',
    application: 'Fachada ventilada edificios corporativos',
    priceUSD: 510, pricePerWp: 1.31,
    isCustom: false, color: '#8b5cf6', brand: 'hiitio',
    regionalCompatibility: { caribe: 3, andina: 3, pacifica: 2, orinoquia: 3, amazonia: 1, insular: 3, notes: 'Fachadas vidriadas premium; 5400 Pa carga frontal' },
  },
  {
    id: 'H08', hiitioId: 'H08', name: 'H08 · HJT Curtain Wall 385W',
    category: 'hjt_curtain',
    description: 'HJT Curtain Wall 385W. Curtain Wall doble vidrio.',
    pmax: 385, voc: 29.65, isc: 16.15, vmp: 25.28, imp: 15.23,
    efficiencySTC: 18.5, tempCoeffPmax: -0.26,
    lengthMm: 1805, widthMm: 1150, weightKg: 67.5,
    noct: 48, systemLoss: 18, degradationAnnual: 0.40,
    pvgisTechchoice: 'crystSi', pvgisMountingplace: 'building',
    application: 'Curtain Wall doble vidrio',
    priceUSD: 500, pricePerWp: 1.30,
    isCustom: false, color: '#a78bfa', brand: 'hiitio',
    regionalCompatibility: { caribe: 3, andina: 3, pacifica: 2, orinoquia: 3, amazonia: 1, insular: 3, notes: 'Fachadas vidriadas premium; 5400 Pa carga frontal' },
  },

  // ===== HJT Wall Tile (H09-H11) =====
  {
    id: 'H09', hiitioId: 'H09', name: 'H09 · HJT Wall Tile 135W',
    category: 'hjt_tile',
    description: 'HJT Wall Tile 135W. Muros ventilados; fachada compacta con marco aluminio 6005-T5.',
    pmax: 135, voc: 10.44, isc: 16.19, vmp: 8.80, imp: 15.35,
    efficiencySTC: 17.7, tempCoeffPmax: -0.26,
    lengthMm: 1580, widthMm: 522, weightKg: 10.5,
    noct: 50, systemLoss: 18, degradationAnnual: 0.45,
    pvgisTechchoice: 'crystSi', pvgisMountingplace: 'building',
    application: 'Muros ventilados; fachada compacta con marco aluminio',
    priceUSD: 185, pricePerWp: 1.37,
    isCustom: false, color: '#0891b2', brand: 'hiitio',
    regionalCompatibility: { caribe: 2, andina: 3, pacifica: 3, orinoquia: 2, amazonia: 1, insular: 2, notes: 'Marco AL estructural; modular; respuesta a difusa' },
  },
  {
    id: 'H10', hiitioId: 'H10', name: 'H10 · HJT Wall Tile 130W',
    category: 'hjt_tile',
    description: 'HJT Wall Tile 130W. Fachada modular con marco AL 6005-T5.',
    pmax: 130, voc: 10.42, isc: 15.95, vmp: 8.60, imp: 15.12,
    efficiencySTC: 17.1, tempCoeffPmax: -0.26,
    lengthMm: 1580, widthMm: 522, weightKg: 10.5,
    noct: 50, systemLoss: 18, degradationAnnual: 0.45,
    pvgisTechchoice: 'crystSi', pvgisMountingplace: 'building',
    application: 'Fachada modular con marco AL 6005-T5',
    priceUSD: 180, pricePerWp: 1.38,
    isCustom: false, color: '#06b6d4', brand: 'hiitio',
    regionalCompatibility: { caribe: 2, andina: 3, pacifica: 3, orinoquia: 2, amazonia: 1, insular: 2, notes: 'Marco AL estructural; modular; respuesta a difusa' },
  },
  {
    id: 'H11', hiitioId: 'H11', name: 'H11 · HJT Wall Tile 125W',
    category: 'hjt_tile',
    description: 'HJT Wall Tile 125W. Fachada compacta integración envolvente.',
    pmax: 125, voc: 10.39, isc: 15.78, vmp: 8.35, imp: 14.98,
    efficiencySTC: 16.5, tempCoeffPmax: -0.26,
    lengthMm: 1580, widthMm: 522, weightKg: 10.5,
    noct: 50, systemLoss: 18, degradationAnnual: 0.45,
    pvgisTechchoice: 'crystSi', pvgisMountingplace: 'building',
    application: 'Fachada compacta integración envolvente',
    priceUSD: 175, pricePerWp: 1.40,
    isCustom: false, color: '#22d3ee', brand: 'hiitio',
    regionalCompatibility: { caribe: 2, andina: 3, pacifica: 3, orinoquia: 2, amazonia: 1, insular: 2, notes: 'Marco AL estructural; modular; respuesta a difusa' },
  },

  // ===== CdTe Semitransparente (H12-H15) =====
  {
    id: 'H12', hiitioId: 'H12', name: 'H12 · CdTe 0% Transp. 115W',
    category: 'cdte_semit',
    description: 'CdTe opaco 115W. Lucernarios opacos, cubiertas semicerradas. Voc 125.5V (strings cortos).',
    pmax: 115, voc: 125.5, isc: 1.24, vmp: 101.8, imp: 1.13,
    efficiencySTC: 15.97, tempCoeffPmax: -0.29,
    lengthMm: 1200, widthMm: 600, weightKg: 12,
    noct: 46, systemLoss: 18, degradationAnnual: 0.40,
    pvgisTechchoice: 'CdTe', pvgisMountingplace: 'building',
    application: 'Lucernarios opacos, cubiertas semicerradas',
    priceUSD: 165, pricePerWp: 1.43,
    isCustom: false, color: '#059669', brand: 'hiitio',
    regionalCompatibility: { caribe: 3, andina: 3, pacifica: 2, orinoquia: 2, amazonia: 1, insular: 3, notes: 'Lucernarios; Voc 125V cadenas cortas; control térmico' },
  },
  {
    id: 'H13', hiitioId: 'H13', name: 'H13 · CdTe 20% Transp. 92W',
    category: 'cdte_semit',
    description: 'CdTe semitransparente 20%, 92W. Fachada con visión exterior. Voc 125.5V.',
    pmax: 92, voc: 125.5, isc: 0.99, vmp: 101.8, imp: 0.90,
    efficiencySTC: 12.78, tempCoeffPmax: -0.29,
    lengthMm: 1200, widthMm: 600, weightKg: 12,
    noct: 46, systemLoss: 18, degradationAnnual: 0.40,
    pvgisTechchoice: 'CdTe', pvgisMountingplace: 'building',
    application: 'Fachada semitransparente con visión exterior',
    priceUSD: 175, pricePerWp: 1.90,
    isCustom: false, color: '#10b981', brand: 'hiitio',
    regionalCompatibility: { caribe: 3, andina: 3, pacifica: 2, orinoquia: 2, amazonia: 1, insular: 3, notes: 'Lucernarios; Voc 125V cadenas cortas; control térmico' },
  },
  {
    id: 'H14', hiitioId: 'H14', name: 'H14 · CdTe 40% Transp. 69W',
    category: 'cdte_semit',
    description: 'CdTe semitransparente 40%, 69W. Balance generación-luz natural. Voc 125.5V.',
    pmax: 69, voc: 125.5, isc: 0.74, vmp: 101.8, imp: 0.68,
    efficiencySTC: 9.58, tempCoeffPmax: -0.29,
    lengthMm: 1200, widthMm: 600, weightKg: 12,
    noct: 46, systemLoss: 18, degradationAnnual: 0.40,
    pvgisTechchoice: 'CdTe', pvgisMountingplace: 'building',
    application: 'Fachada con balance generación-luz natural',
    priceUSD: 185, pricePerWp: 2.68,
    isCustom: false, color: '#34d399', brand: 'hiitio',
    regionalCompatibility: { caribe: 3, andina: 3, pacifica: 2, orinoquia: 2, amazonia: 1, insular: 3, notes: 'Lucernarios; Voc 125V cadenas cortas; control térmico' },
  },
  {
    id: 'H15', hiitioId: 'H15', name: 'H15 · CdTe 60% Transp. 46W',
    category: 'cdte_semit',
    description: 'CdTe alta transparencia 60%, 46W. Vidrio solar arquitectónico con máxima visibilidad. Voc 125.5V.',
    pmax: 46, voc: 125.5, isc: 0.50, vmp: 101.8, imp: 0.45,
    efficiencySTC: 6.39, tempCoeffPmax: -0.29,
    lengthMm: 1200, widthMm: 600, weightKg: 12,
    noct: 46, systemLoss: 18, degradationAnnual: 0.40,
    pvgisTechchoice: 'CdTe', pvgisMountingplace: 'building',
    application: 'Vidrio solar arquitectónico con máxima visibilidad',
    priceUSD: 195, pricePerWp: 4.24,
    isCustom: false, color: '#6ee7b7', brand: 'hiitio',
    regionalCompatibility: { caribe: 3, andina: 3, pacifica: 2, orinoquia: 2, amazonia: 1, insular: 3, notes: 'Lucernarios; Voc 125V cadenas cortas; control térmico' },
  },

  // ===== CdTe BIPV Arquitectónico (H16) =====
  {
    id: 'H16', hiitioId: 'H16', name: 'H16 · CdTe BIPV Estructural 85W',
    category: 'cdte_bipv',
    description: 'CdTe BIPV vidrio estructural 5mm, 20% transparencia, 85W. Voc 122.8V. Granizo Nivel IV.',
    pmax: 85, voc: 122.8, isc: 0.95, vmp: 98.5, imp: 0.88,
    efficiencySTC: 11.81, tempCoeffPmax: -0.29,
    lengthMm: 1200, widthMm: 600, weightKg: 29,
    noct: 48, systemLoss: 18, degradationAnnual: 0.40,
    pvgisTechchoice: 'CdTe', pvgisMountingplace: 'building',
    application: 'Fachada BIPV vidrio estructural 5 mm; granizo Nivel IV',
    priceUSD: 210, pricePerWp: 2.47,
    isCustom: false, color: '#047857', brand: 'hiitio',
    regionalCompatibility: { caribe: 3, andina: 3, pacifica: 2, orinoquia: 2, amazonia: 1, insular: 3, notes: 'Vidrio estructural 5-22 mm; granizo Nivel IV' },
  },

  // ===== CIGS Teja Curva (H17) =====
  {
    id: 'H17', hiitioId: 'H17', name: 'H17 · CIGS Teja Curva Negra 32W',
    category: 'cigs',
    description: 'Teja curva CIGS negra 32W. Ligera 6.5 kg. Cubierta inclinada residencial estética patrimonial. Colores: Negro/Rojo/Verde.',
    pmax: 32, voc: 10.8, isc: 4.10, vmp: 8.90, imp: 3.60,
    efficiencySTC: 8.89, tempCoeffPmax: -0.30,
    lengthMm: 720, widthMm: 500, weightKg: 6.5,
    noct: 45, systemLoss: 18, degradationAnnual: 0.60,
    pvgisTechchoice: 'CIS', pvgisMountingplace: 'building',
    application: 'Cubierta inclinada residencial estética patrimonial',
    priceUSD: 65, pricePerWp: 2.03,
    isCustom: false, color: '#d97706', brand: 'hiitio',
    regionalCompatibility: { caribe: 2, andina: 3, pacifica: 2, orinoquia: 1, amazonia: 2, insular: 2, notes: 'Patrimonial; ligera 6.5 kg/pieza; baja eficiencia ~10%' },
  },

  // ===== EINNOVA — Antirreflejo (TOPCon N) =====
  {
    id: 'P01', hiitioId: 'P01', name: 'P01 · EINNOVA Antirreflejo ESM-455T (TOPCon N)',
    category: 'einnova_antirreflejo', brand: 'einnova',
    description: '455W TOPCon N antirreflejo. Mejor captación de difusa; tropicalizado salt-spray.',
    pmax: 455, voc: 41.2, isc: 13.82, vmp: 36.34, imp: 13.25,
    efficiencySTC: 23.3, tempCoeffPmax: -0.31,
    lengthMm: 1722, widthMm: 1134, weightKg: 21,
    noct: 45, systemLoss: 18, degradationAnnual: 0.40,
    pvgisTechchoice: 'crystSi', pvgisMountingplace: 'building',
    application: 'Cubiertas residenciales/comerciales premium, baja molestia óptica',
    priceUSD: 250, pricePerWp: 0.55,
    isCustom: false, color: '#0066CC',
    regionalCompatibility: { caribe: 3, andina: 3, pacifica: 3, orinoquia: 3, amazonia: 2, insular: 3, notes: 'Mejor captación de difusa; tropicalizado salt-spray' },
  },

  // ===== EINNOVA — Bifacial N-Type =====
  {
    id: 'P02', hiitioId: 'P02', name: 'P02 · EINNOVA Bifacial ESM-580 N-Type',
    category: 'einnova_bifacial', brand: 'einnova',
    description: '580W bifacial N-Type. Cubiertas planas comerciales, agrovoltaico Llanos/Caribe.',
    pmax: 580, voc: 51, isc: 14.39, vmp: 42.19, imp: 13.75,
    efficiencySTC: 22.44, tempCoeffPmax: -0.36,
    lengthMm: 2279, widthMm: 1134, weightKg: 28,
    noct: 45, systemLoss: 18, degradationAnnual: 0.40,
    pvgisTechchoice: 'crystSi', pvgisMountingplace: 'free',
    application: 'Cubiertas planas comerciales, agrovoltaico Llanos/Caribe',
    priceUSD: 300, pricePerWp: 0.52,
    isCustom: false, color: '#0077DD',
    regionalCompatibility: { caribe: 3, andina: 1, pacifica: 1, orinoquia: 3, amazonia: 1, insular: 2, notes: 'Cubiertas planas, agrovoltaico' },
  },

  // ===== EINNOVA — Teja BC (Negra/Terracota) =====
  {
    id: 'P04', hiitioId: 'P04', name: 'P04 · EINNOVA Teja BC ESM-70 Negra',
    category: 'einnova_teja_bc', brand: 'einnova',
    description: '70W teja BC negra. Cubierta residencial premium estilo elegante negro.',
    pmax: 70, voc: 12.95, isc: 6.56, vmp: 11.25, imp: 6.22,
    efficiencySTC: 20.17, tempCoeffPmax: -0.31,
    lengthMm: 535, widthMm: 535, weightKg: 4.5,
    noct: 45, systemLoss: 18, degradationAnnual: 0.45,
    pvgisTechchoice: 'crystSi', pvgisMountingplace: 'building',
    application: 'Cubierta residencial premium estilo elegante negro',
    priceUSD: 85, pricePerWp: 1.21,
    isCustom: false, color: '#1a1a2e',
    regionalCompatibility: { caribe: 3, andina: 3, pacifica: 2, orinoquia: 1, amazonia: 1, insular: 3, notes: 'Estética premium; integración patrimonial' },
  },
  {
    id: 'P06', hiitioId: 'P06', name: 'P06 · EINNOVA Teja BC ESM-68 Negra',
    category: 'einnova_teja_bc', brand: 'einnova',
    description: '68W teja BC negra alternativa. Tejado residencial.',
    pmax: 68, voc: 12.72, isc: 6.51, vmp: 11.02, imp: 6.17,
    efficiencySTC: 19.6, tempCoeffPmax: -0.31,
    lengthMm: 535, widthMm: 535, weightKg: 4.5,
    noct: 45, systemLoss: 18, degradationAnnual: 0.45,
    pvgisTechchoice: 'crystSi', pvgisMountingplace: 'building',
    application: 'Tejado residencial alternativa a ESM-70',
    priceUSD: 80, pricePerWp: 1.18,
    isCustom: false, color: '#2d2d44',
    regionalCompatibility: { caribe: 3, andina: 3, pacifica: 2, orinoquia: 1, amazonia: 1, insular: 3, notes: 'Estética premium; integración patrimonial' },
  },
  {
    id: 'P13', hiitioId: 'P13', name: 'P13 · EINNOVA Teja BC Curva ESM-56W Terracota',
    category: 'einnova_teja_bc', brand: 'einnova',
    description: '56W teja BC curva terracota. Tejado colonial patrimonio histórico.',
    pmax: 56, voc: 12.82, isc: 5.25, vmp: 11.14, imp: 5.03,
    efficiencySTC: 16.14, tempCoeffPmax: -0.31,
    lengthMm: 535, widthMm: 535, weightKg: 4.5,
    noct: 45, systemLoss: 18, degradationAnnual: 0.45,
    pvgisTechchoice: 'crystSi', pvgisMountingplace: 'building',
    application: 'Tejado colonial patrimonio histórico Andina/Caribe',
    priceUSD: 75, pricePerWp: 1.34,
    isCustom: false, color: '#c2703e',
    regionalCompatibility: { caribe: 3, andina: 3, pacifica: 2, orinoquia: 1, amazonia: 1, insular: 3, notes: 'Estética premium; integración patrimonial' },
  },

  // ===== EINNOVA — Teja Plana =====
  {
    id: 'P03', hiitioId: 'P03', name: 'P03 · EINNOVA Teja Plana ESM-FT 120W',
    category: 'einnova_teja_plana', brand: 'einnova',
    description: '120W teja plana. Tejados a dos aguas, casa rural y urbana.',
    pmax: 120, voc: 10.99, isc: 13.26, vmp: 9.59, imp: 12.5,
    efficiencySTC: 21.8, tempCoeffPmax: -0.31,
    lengthMm: 1600, widthMm: 460, weightKg: 13.5,
    noct: 45, systemLoss: 18, degradationAnnual: 0.45,
    pvgisTechchoice: 'crystSi', pvgisMountingplace: 'building',
    application: 'Tejados a dos aguas, casa rural y urbana',
    priceUSD: 120, pricePerWp: 1.00,
    isCustom: false, color: '#4a90d9',
    regionalCompatibility: { caribe: 2, andina: 3, pacifica: 2, orinoquia: 1, amazonia: 1, insular: 2, notes: 'Tejados a dos aguas residenciales' },
  },
  {
    id: 'P09', hiitioId: 'P09', name: 'P09 · EINNOVA Teja Plana ESM-90W',
    category: 'einnova_teja_plana', brand: 'einnova',
    description: '90W teja plana estándar. Tejado residencial Andina/Caribe.',
    pmax: 90, voc: 16.53, isc: 6.75, vmp: 14.22, imp: 6.45,
    efficiencySTC: 17.7, tempCoeffPmax: -0.31,
    lengthMm: 1219, widthMm: 417, weightKg: 6,
    noct: 45, systemLoss: 18, degradationAnnual: 0.45,
    pvgisTechchoice: 'crystSi', pvgisMountingplace: 'building',
    application: 'Tejado residencial Andina/Caribe estándar',
    priceUSD: 95, pricePerWp: 1.06,
    isCustom: false, color: '#5ba0e9',
    regionalCompatibility: { caribe: 2, andina: 3, pacifica: 2, orinoquia: 1, amazonia: 1, insular: 2, notes: 'Tejados a dos aguas residenciales' },
  },
  {
    id: 'P12', hiitioId: 'P12', name: 'P12 · EINNOVA Teja Plana ESM-30W',
    category: 'einnova_teja_plana', brand: 'einnova',
    description: '30W teja plana pequeña. Cumbreras, remates de tejado y pequeñas áreas.',
    pmax: 30, voc: 5.51, isc: 6.75, vmp: 4.74, imp: 6.45,
    efficiencySTC: 16.85, tempCoeffPmax: -0.31,
    lengthMm: 427, widthMm: 417, weightKg: 2,
    noct: 45, systemLoss: 18, degradationAnnual: 0.45,
    pvgisTechchoice: 'crystSi', pvgisMountingplace: 'building',
    application: 'Cumbreras, remates de tejado y pequeñas áreas',
    priceUSD: 45, pricePerWp: 1.50,
    isCustom: false, color: '#6cb0f9',
    regionalCompatibility: { caribe: 2, andina: 3, pacifica: 2, orinoquia: 1, amazonia: 1, insular: 2, notes: 'Tejados a dos aguas residenciales' },
  },

  // ===== EINNOVA — Color Panel Cubierta-Fachada =====
  {
    id: 'P05', hiitioId: 'P05', name: 'P05 · EINNOVA Color Panel Orange-Terracota 470W',
    category: 'einnova_color_panel', brand: 'einnova',
    description: '470W color panel terracota. Cubierta-fachada industrial estética cálida.',
    pmax: 470, voc: 36.4, isc: 12.91, vmp: 46.2, imp: 12.26,
    efficiencySTC: 19.79, tempCoeffPmax: -0.35,
    lengthMm: 2094, widthMm: 1134, weightKg: 25,
    noct: 45, systemLoss: 18, degradationAnnual: 0.45,
    pvgisTechchoice: 'crystSi', pvgisMountingplace: 'building',
    application: 'Cubierta-fachada industrial estética cálida',
    priceUSD: 280, pricePerWp: 0.60,
    isCustom: false, color: '#e67e22',
    regionalCompatibility: { caribe: 2, andina: 3, pacifica: 2, orinoquia: 2, amazonia: 1, insular: 2, notes: 'Estética industrial; cubierta+fachada' },
  },

  // ===== EINNOVA — Fachada BIPV =====
  {
    id: 'P08', hiitioId: 'P08', name: 'P08 · EINNOVA Fachada BIPV Modelo 3 (1716×1128)',
    category: 'einnova_fachada', brand: 'einnova',
    description: '360W fachada BIPV negra. Fachada ventilada edificios oficinas Andina.',
    pmax: 360, voc: 36.18, isc: 14.14, vmp: 28.62, imp: 12.58,
    efficiencySTC: 18.6, tempCoeffPmax: -0.31,
    lengthMm: 1716, widthMm: 1128, weightKg: 34,
    noct: 48, systemLoss: 18, degradationAnnual: 0.40,
    pvgisTechchoice: 'crystSi', pvgisMountingplace: 'building',
    application: 'Fachada ventilada edificios oficinas Andina',
    priceUSD: 400, pricePerWp: 1.11,
    isCustom: false, color: '#2c3e50',
    regionalCompatibility: { caribe: 2, andina: 3, pacifica: 2, orinoquia: 1, amazonia: 1, insular: 3, notes: 'Edificios oficinas/hoteles; varios colores' },
  },
  {
    id: 'P10', hiitioId: 'P10', name: 'P10 · EINNOVA Fachada BIPV Modelo 1 (1530×1000)',
    category: 'einnova_fachada', brand: 'einnova',
    description: '270W fachada BIPV negra panel grande modular.',
    pmax: 270, voc: 26.8, isc: 14.1, vmp: 21.2, imp: 12.73,
    efficiencySTC: 17.6, tempCoeffPmax: -0.31,
    lengthMm: 1530, widthMm: 1000, weightKg: 26.5,
    noct: 48, systemLoss: 18, degradationAnnual: 0.40,
    pvgisTechchoice: 'crystSi', pvgisMountingplace: 'building',
    application: 'Fachada ventilada panel grande modular',
    priceUSD: 320, pricePerWp: 1.19,
    isCustom: false, color: '#34495e',
    regionalCompatibility: { caribe: 2, andina: 3, pacifica: 2, orinoquia: 1, amazonia: 1, insular: 3, notes: 'Edificios oficinas/hoteles; varios colores' },
  },
  {
    id: 'P11', hiitioId: 'P11', name: 'P11 · EINNOVA Fachada BIPV Modelo 2 (1160×400)',
    category: 'einnova_fachada', brand: 'einnova',
    description: '80W fachada urbana pieza pequeña personalizable.',
    pmax: 80, voc: 16.08, isc: 7.01, vmp: 12.72, imp: 6.28,
    efficiencySTC: 17.2, tempCoeffPmax: -0.31,
    lengthMm: 1160, widthMm: 400, weightKg: 8.5,
    noct: 48, systemLoss: 18, degradationAnnual: 0.40,
    pvgisTechchoice: 'crystSi', pvgisMountingplace: 'building',
    application: 'Fachada urbana pieza pequeña personalizable',
    priceUSD: 120, pricePerWp: 1.50,
    isCustom: false, color: '#4a6fa5',
    regionalCompatibility: { caribe: 2, andina: 3, pacifica: 2, orinoquia: 1, amazonia: 1, insular: 3, notes: 'Edificios oficinas/hoteles; varios colores' },
  },

  // ===== EINNOVA — Flexible =====
  {
    id: 'P07', hiitioId: 'P07', name: 'P07 · EINNOVA Flexible ESM-140W (apertura)',
    category: 'einnova_flexible', brand: 'einnova',
    description: '140W flexible apertura. Cubiertas curvas, baja capacidad portante.',
    pmax: 140, voc: 40.9, isc: 4.41, vmp: 33.9, imp: 4.1,
    efficiencySTC: 18.3, tempCoeffPmax: -0.31,
    lengthMm: 2583, widthMm: 348, weightKg: 1.7,
    noct: 43, systemLoss: 18, degradationAnnual: 0.50,
    pvgisTechchoice: 'crystSi', pvgisMountingplace: 'building',
    application: 'Cubiertas curvas, baja capacidad portante',
    priceUSD: 150, pricePerWp: 1.07,
    isCustom: false, color: '#27ae60',
    regionalCompatibility: { caribe: 2, andina: 1, pacifica: 3, orinoquia: 1, amazonia: 3, insular: 2, notes: 'Baja capacidad portante; off-grid amazónico' },
  },
  {
    id: 'P14', hiitioId: 'P14', name: 'P14 · EINNOVA Flexible ESM-250 (TOPCon N)',
    category: 'einnova_flexible', brand: 'einnova',
    description: '250W flexible TOPCon N. Balcones, cubiertas selva amazónica, palafítica.',
    pmax: 250, voc: 44.4, isc: 6.82, vmp: 39.5, imp: 6.33,
    efficiencySTC: 21.2, tempCoeffPmax: -0.31,
    lengthMm: 1025, widthMm: 1153, weightKg: 3.5,
    noct: 43, systemLoss: 18, degradationAnnual: 0.50,
    pvgisTechchoice: 'crystSi', pvgisMountingplace: 'building',
    application: 'Balcones, cubiertas selva amazónica, palafítica',
    priceUSD: 200, pricePerWp: 0.80,
    isCustom: false, color: '#2ecc71',
    regionalCompatibility: { caribe: 2, andina: 1, pacifica: 3, orinoquia: 1, amazonia: 3, insular: 2, notes: 'Baja capacidad portante; off-grid amazónico' },
  },

  // ===== EINNOVA — AgriPV Transparente =====
  {
    id: 'P15', hiitioId: 'P15', name: 'P15 · EINNOVA AgriPV Transparente 345W (42% T)',
    category: 'einnova_agripv', brand: 'einnova',
    description: '345W AgriPV 42% transparencia. Invernaderos, cubiertas agrícolas, claraboyas.',
    pmax: 345, voc: 31.4, isc: 13.42, vmp: 27.06, imp: 12.75,
    efficiencySTC: 13.36, tempCoeffPmax: -0.29,
    lengthMm: 2278, widthMm: 1134, weightKg: 31.6,
    noct: 44, systemLoss: 18, degradationAnnual: 0.40,
    pvgisTechchoice: 'crystSi', pvgisMountingplace: 'building',
    application: 'Invernaderos, cubiertas agrícolas, claraboyas',
    priceUSD: 350, pricePerWp: 1.01,
    isCustom: false, color: '#f39c12',
    regionalCompatibility: { caribe: 2, andina: 1, pacifica: 1, orinoquia: 3, amazonia: 2, insular: 1, notes: 'Invernaderos, palma, ganadería' },
  },
  {
    id: 'P17', hiitioId: 'P17', name: 'P17 · EINNOVA AgriPV Transparente 250W (58% T)',
    category: 'einnova_agripv', brand: 'einnova',
    description: '250W AgriPV 58% transparencia. Cultivos sensibles a sombra, máxima transmitancia.',
    pmax: 250, voc: 22.8, isc: 13.41, vmp: 19.64, imp: 12.73,
    efficiencySTC: 9.68, tempCoeffPmax: -0.29,
    lengthMm: 2278, widthMm: 1134, weightKg: 31.6,
    noct: 44, systemLoss: 18, degradationAnnual: 0.40,
    pvgisTechchoice: 'crystSi', pvgisMountingplace: 'building',
    application: 'Cultivos sensibles a sombra, máxima transmitancia',
    priceUSD: 300, pricePerWp: 1.20,
    isCustom: false, color: '#f1c40f',
    regionalCompatibility: { caribe: 2, andina: 1, pacifica: 1, orinoquia: 3, amazonia: 2, insular: 1, notes: 'Invernaderos, palma, ganadería' },
  },

  // ===== EINNOVA — Pavimento Solar =====
  {
    id: 'P16', hiitioId: 'P16', name: 'P16 · EINNOVA Pavimento ESM-110W Solar',
    category: 'einnova_pavimento', brand: 'einnova',
    description: '110W pavimento solar. Plazas, andenes peatonales, estaciones servicio.',
    pmax: 110, voc: 11.08, isc: 12.35, vmp: 9.34, imp: 11.8,
    efficiencySTC: 9.6, tempCoeffPmax: -0.31,
    lengthMm: 1500, widthMm: 425, weightKg: 27,
    noct: 50, systemLoss: 20, degradationAnnual: 0.50,
    pvgisTechchoice: 'crystSi', pvgisMountingplace: 'building',
    application: 'Plazas, andenes peatonales, estaciones servicio',
    priceUSD: 200, pricePerWp: 1.82,
    isCustom: false, color: '#95a5a6',
    regionalCompatibility: { caribe: 2, andina: 2, pacifica: 1, orinoquia: 2, amazonia: 1, insular: 2, notes: 'Plazas, estaciones servicio, urbanismo' },
  },

  // ===== EINNOVA — Vidrio FV =====
  {
    id: 'P18', hiitioId: 'P18', name: 'P18 · EINNOVA Vidrio FV 40% T (58W)',
    category: 'einnova_vidrio', brand: 'einnova',
    description: '58W vidrio FV 40% transparencia. Claraboyas, fachadas curtain wall LEED/EDGE.',
    pmax: 58, voc: 122.5, isc: 0.66, vmp: 98, imp: 0.58,
    efficiencySTC: 7.0, tempCoeffPmax: -0.214,
    lengthMm: 1200, widthMm: 600, weightKg: 11.8,
    noct: 46, systemLoss: 18, degradationAnnual: 0.40,
    pvgisTechchoice: 'CdTe', pvgisMountingplace: 'building',
    application: 'Claraboyas, fachadas curtain wall LEED/EDGE',
    priceUSD: 180, pricePerWp: 3.10,
    isCustom: false, color: '#3498db',
    regionalCompatibility: { caribe: 3, andina: 3, pacifica: 2, orinoquia: 2, amazonia: 1, insular: 3, notes: 'Claraboyas, curtain wall LEED/EDGE' },
  },

  // ===== Tecnologías Genéricas de Referencia =====
  {
    id: 'GEN_CSI', hiitioId: '', name: 'Genérico · c-Si Mono PERC',
    category: 'generic',
    description: 'Panel silicio cristalino monocristalino PERC estándar de referencia. Tecnología más común en instalaciones convencionales.',
    pmax: 550, voc: 49.5, isc: 14.0, vmp: 41.5, imp: 13.25,
    efficiencySTC: 21.5, tempCoeffPmax: -0.35,
    lengthMm: 2278, widthMm: 1134, weightKg: 27.5,
    noct: 45, systemLoss: 14, degradationAnnual: 0.45,
    pvgisTechchoice: 'crystSi', pvgisMountingplace: 'free',
    application: 'Instalaciones convencionales en cubierta (rack abierto)',
    priceUSD: 165, pricePerWp: 0.30,
    isCustom: false, color: '#6b7280', brand: 'generic',
  },
  {
    id: 'GEN_HJT', hiitioId: '', name: 'Genérico · HJT Heterojunción',
    category: 'generic',
    description: 'Panel HJT genérico de referencia. Excelente coeficiente de temperatura, ideal para climas cálidos.',
    pmax: 600, voc: 52.0, isc: 14.5, vmp: 43.5, imp: 13.8,
    efficiencySTC: 22.5, tempCoeffPmax: -0.26,
    lengthMm: 2278, widthMm: 1134, weightKg: 28.0,
    noct: 42, systemLoss: 14, degradationAnnual: 0.35,
    pvgisTechchoice: 'crystSi', pvgisMountingplace: 'free',
    application: 'Instalaciones convencionales, climas cálidos',
    priceUSD: 210, pricePerWp: 0.35,
    isCustom: false, color: '#9ca3af', brand: 'generic',
  },
  {
    id: 'GEN_CDTE', hiitioId: '', name: 'Genérico · CdTe (First Solar)',
    category: 'generic',
    description: 'Panel CdTe genérico de referencia (tipo First Solar). Buen rendimiento en alta temperatura y baja irradiancia.',
    pmax: 460, voc: 219.0, isc: 2.54, vmp: 182.0, imp: 2.53,
    efficiencySTC: 19.3, tempCoeffPmax: -0.28,
    lengthMm: 2009, widthMm: 1232, weightKg: 32.0,
    noct: 44, systemLoss: 14, degradationAnnual: 0.40,
    pvgisTechchoice: 'CdTe', pvgisMountingplace: 'free',
    application: 'Instalaciones a gran escala, climas cálidos',
    priceUSD: 175, pricePerWp: 0.38,
    isCustom: false, color: '#d1d5db', brand: 'generic',
  },
  // ===== SOLTECH — DVH Doble Vidrio (ASP-DVH) =====
  {
    id: 'SOL_DVH_T0', hiitioId: '', name: 'SOLTECH · ASP-DVH-T0 (216W)',
    category: 'soltech_dvh',
    description: 'Doble Vidrio Hermético BIPV 0% transparencia. Aislamiento térmico y acústico reforzado (U=4.89, SC=0.29).',
    pmax: 216, voc: 181.4, isc: 1.39, vmp: 150.0, imp: 1.25,
    efficiencySTC: 15.0, tempCoeffPmax: -0.321,
    lengthMm: 1200, widthMm: 1200, weightKg: 60.0,
    noct: 46, systemLoss: 14, degradationAnnual: 0.40,
    pvgisTechchoice: 'CdTe', pvgisMountingplace: 'building',
    application: 'Ventanas fijas y muros cortina con aislamiento térmico reforzado',
    priceUSD: 480, pricePerWp: 2.22,
    isCustom: false, color: '#d97706', brand: 'soltech',
  },
  {
    id: 'SOL_DVH_T10', hiitioId: '', name: 'SOLTECH · ASP-DVH-T10 (194W)',
    category: 'soltech_dvh',
    description: 'Doble Vidrio Hermético BIPV 10% transparencia. Confort visual y aislamiento (U=4.89, SC=0.32).',
    pmax: 194, voc: 181.4, isc: 1.19, vmp: 150.0, imp: 1.12,
    efficiencySTC: 13.5, tempCoeffPmax: -0.321,
    lengthMm: 1200, widthMm: 1200, weightKg: 60.0,
    noct: 46, systemLoss: 14, degradationAnnual: 0.40,
    pvgisTechchoice: 'CdTe', pvgisMountingplace: 'building',
    application: 'Fachadas vidriadas, lucernarios de baja transparencia',
    priceUSD: 490, pricePerWp: 2.53,
    isCustom: false, color: '#d97706', brand: 'soltech',
  },
  {
    id: 'SOL_DVH_T30', hiitioId: '', name: 'SOLTECH · ASP-DVH-T30 (151W)',
    category: 'soltech_dvh',
    description: 'Doble Vidrio Hermético BIPV 30% transparencia. Óptimo balance luz/generación (U=4.89, SC=0.41).',
    pmax: 151, voc: 181.4, isc: 0.93, vmp: 150.0, imp: 0.88,
    efficiencySTC: 10.5, tempCoeffPmax: -0.321,
    lengthMm: 1200, widthMm: 1200, weightKg: 60.0,
    noct: 46, systemLoss: 14, degradationAnnual: 0.40,
    pvgisTechchoice: 'CdTe', pvgisMountingplace: 'building',
    application: 'Fachadas, ventanas de oficinas y áreas de trabajo',
    priceUSD: 510, pricePerWp: 3.38,
    isCustom: false, color: '#d97706', brand: 'soltech',
  },
  {
    id: 'SOL_DVH_T50', hiitioId: '', name: 'SOLTECH · ASP-DVH-T50 (108W)',
    category: 'soltech_dvh',
    description: 'Doble Vidrio Hermético BIPV 50% transparencia. Alta luminosidad para fachadas y ventanas (U=4.89, SC=0.53).',
    pmax: 108, voc: 181.4, isc: 0.66, vmp: 150.0, imp: 0.62,
    efficiencySTC: 7.5, tempCoeffPmax: -0.321,
    lengthMm: 1200, widthMm: 1200, weightKg: 60.0,
    noct: 46, systemLoss: 14, degradationAnnual: 0.40,
    pvgisTechchoice: 'CdTe', pvgisMountingplace: 'building',
    application: 'Ventanas y áreas residenciales con requerimiento de luz natural',
    priceUSD: 530, pricePerWp: 4.91,
    isCustom: false, color: '#d97706', brand: 'soltech',
  },
  {
    id: 'SOL_DVH_T60', hiitioId: '', name: 'SOLTECH · ASP-DVH-T60 (84W)',
    category: 'soltech_dvh',
    description: 'Doble Vidrio Hermético BIPV 60% transparencia. Máxima transmisión de luz (U=4.89, SC=0.57).',
    pmax: 84, voc: 181.4, isc: 0.53, vmp: 150.0, imp: 0.49,
    efficiencySTC: 5.8, tempCoeffPmax: -0.321,
    lengthMm: 1200, widthMm: 1200, weightKg: 60.0,
    noct: 46, systemLoss: 14, degradationAnnual: 0.40,
    pvgisTechchoice: 'CdTe', pvgisMountingplace: 'building',
    application: 'Muros cortina con alta visibilidad y confort térmico',
    priceUSD: 540, pricePerWp: 6.43,
    isCustom: false, color: '#d97706', brand: 'soltech',
  },
  {
    id: 'SOL_DVH_T70', hiitioId: '', name: 'SOLTECH · ASP-DVH-T70 (62W)',
    category: 'soltech_dvh',
    description: 'Doble Vidrio Hermético BIPV 70% transparencia. Vista panorámica y control térmico (U=4.89, SC=0.62).',
    pmax: 62, voc: 181.4, isc: 0.40, vmp: 150.0, imp: 0.36,
    efficiencySTC: 4.3, tempCoeffPmax: -0.321,
    lengthMm: 1200, widthMm: 1200, weightKg: 60.0,
    noct: 46, systemLoss: 14, degradationAnnual: 0.40,
    pvgisTechchoice: 'CdTe', pvgisMountingplace: 'building',
    application: 'Grandes ventanales, vitrinas y fachadas norte/sur',
    priceUSD: 550, pricePerWp: 8.87,
    isCustom: false, color: '#d97706', brand: 'soltech',
  },
  // ===== SOLTECH — Laminated Vidrio (ASP-LAM3) =====
  {
    id: 'SOL_LAM3_T0_1200', hiitioId: '', name: 'SOLTECH · ASP-LAM3-T0 (1200x1200mm, 216W)',
    category: 'soltech_laminado',
    description: 'Vidrio laminado BIPV 1200x1200mm, 0% transparencia. Máxima densidad de potencia.',
    pmax: 216, voc: 181.4, isc: 1.39, vmp: 150.0, imp: 1.25,
    efficiencySTC: 15.0, tempCoeffPmax: -0.321,
    lengthMm: 1200, widthMm: 1200, weightKg: 52.0,
    noct: 45, systemLoss: 14, degradationAnnual: 0.40,
    pvgisTechchoice: 'CdTe', pvgisMountingplace: 'building',
    application: 'Revestimiento de fachadas, antepechos y lucernarios opacos',
    priceUSD: 360, pricePerWp: 1.67,
    isCustom: false, color: '#d97706', brand: 'soltech',
  },
  {
    id: 'SOL_LAM3_T10_1200', hiitioId: '', name: 'SOLTECH · ASP-LAM3-T10 (1200x1200mm, 194W)',
    category: 'soltech_laminado',
    description: 'Vidrio laminado BIPV 1200x1200mm, 10% transparencia.',
    pmax: 194, voc: 181.4, isc: 1.19, vmp: 150.0, imp: 1.12,
    efficiencySTC: 13.5, tempCoeffPmax: -0.321,
    lengthMm: 1200, widthMm: 1200, weightKg: 52.0,
    noct: 45, systemLoss: 14, degradationAnnual: 0.40,
    pvgisTechchoice: 'CdTe', pvgisMountingplace: 'building',
    application: 'Pérgolas, marquesinas de acceso, control de deslumbramiento',
    priceUSD: 370, pricePerWp: 1.91,
    isCustom: false, color: '#d97706', brand: 'soltech',
  },
  {
    id: 'SOL_LAM3_T20_1200', hiitioId: '', name: 'SOLTECH · ASP-LAM3-T20 (1200x1200mm, 173W)',
    category: 'soltech_laminado',
    description: 'Vidrio laminado BIPV 1200x1200mm, 20% transparencia.',
    pmax: 173, voc: 181.4, isc: 1.07, vmp: 150.0, imp: 1.01,
    efficiencySTC: 12.0, tempCoeffPmax: -0.321,
    lengthMm: 1200, widthMm: 1200, weightKg: 52.0,
    noct: 45, systemLoss: 14, degradationAnnual: 0.40,
    pvgisTechchoice: 'CdTe', pvgisMountingplace: 'building',
    application: 'Cubiertas de vidrio comerciales, pérgolas de sombreado',
    priceUSD: 380, pricePerWp: 2.20,
    isCustom: false, color: '#d97706', brand: 'soltech',
  },
  {
    id: 'SOL_LAM3_T30_1200', hiitioId: '', name: 'SOLTECH · ASP-LAM3-T30 (1200x1200mm, 151W)',
    category: 'soltech_laminado',
    description: 'Vidrio laminado BIPV 1200x1200mm, 30% transparencia.',
    pmax: 151, voc: 181.4, isc: 0.93, vmp: 150.0, imp: 0.88,
    efficiencySTC: 10.5, tempCoeffPmax: -0.321,
    lengthMm: 1200, widthMm: 1200, weightKg: 52.0,
    noct: 45, systemLoss: 14, degradationAnnual: 0.40,
    pvgisTechchoice: 'CdTe', pvgisMountingplace: 'building',
    application: 'Pasamanos, barandas de balcones y parasoles en fachada',
    priceUSD: 395, pricePerWp: 2.62,
    isCustom: false, color: '#d97706', brand: 'soltech',
  },
  {
    id: 'SOL_LAM3_T40_1200', hiitioId: '', name: 'SOLTECH · ASP-LAM3-T40 (1200x1200mm, 130W)',
    category: 'soltech_laminado',
    description: 'Vidrio laminado BIPV 1200x1200mm, 40% transparencia.',
    pmax: 130, voc: 181.4, isc: 0.80, vmp: 150.0, imp: 0.76,
    efficiencySTC: 9.0, tempCoeffPmax: -0.321,
    lengthMm: 1200, widthMm: 1200, weightKg: 52.0,
    noct: 45, systemLoss: 14, degradationAnnual: 0.40,
    pvgisTechchoice: 'CdTe', pvgisMountingplace: 'building',
    application: 'Claraboyas de gran tamaño, atrios y pasarelas cubiertas',
    priceUSD: 410, pricePerWp: 3.15,
    isCustom: false, color: '#d97706', brand: 'soltech',
  },
  {
    id: 'SOL_LAM3_T50_1200', hiitioId: '', name: 'SOLTECH · ASP-LAM3-T50 (1200x1200mm, 108W)',
    category: 'soltech_laminado',
    description: 'Vidrio laminado BIPV 1200x1200mm, 50% transparencia.',
    pmax: 108, voc: 181.4, isc: 0.66, vmp: 150.0, imp: 0.62,
    efficiencySTC: 7.5, tempCoeffPmax: -0.321,
    lengthMm: 1200, widthMm: 1200, weightKg: 52.0,
    noct: 45, systemLoss: 14, degradationAnnual: 0.40,
    pvgisTechchoice: 'CdTe', pvgisMountingplace: 'building',
    application: 'Vidrios de fachada translucida, atrios residenciales',
    priceUSD: 420, pricePerWp: 3.89,
    isCustom: false, color: '#d97706', brand: 'soltech',
  },
  {
    id: 'SOL_LAM3_T0_1800', hiitioId: '', name: 'SOLTECH · ASP-LAM3-T0 (1200x1800mm, 326W)',
    category: 'soltech_laminado',
    description: 'Vidrio laminado BIPV 1200x1800mm, 0% transparencia. Alta potencia para áreas rectangulares grandes.',
    pmax: 326, voc: 181.4, isc: 2.10, vmp: 150.0, imp: 1.88,
    efficiencySTC: 15.1, tempCoeffPmax: -0.321,
    lengthMm: 1800, widthMm: 1200, weightKg: 89.0,
    noct: 45, systemLoss: 14, degradationAnnual: 0.40,
    pvgisTechchoice: 'CdTe', pvgisMountingplace: 'building',
    application: 'Revestimiento de fachadas altas y muros ciegos',
    priceUSD: 540, pricePerWp: 1.66,
    isCustom: false, color: '#d97706', brand: 'soltech',
  },
  {
    id: 'SOL_LAM3_T30_1800', hiitioId: '', name: 'SOLTECH · ASP-LAM3-T30 (1200x1800mm, 228W)',
    category: 'soltech_laminado',
    description: 'Vidrio laminado BIPV 1200x1800mm, 30% transparencia. Formato vertical panorámico.',
    pmax: 228, voc: 181.4, isc: 1.40, vmp: 150.0, imp: 1.30,
    efficiencySTC: 10.6, tempCoeffPmax: -0.321,
    lengthMm: 1800, widthMm: 1200, weightKg: 89.0,
    noct: 45, systemLoss: 14, degradationAnnual: 0.40,
    pvgisTechchoice: 'CdTe', pvgisMountingplace: 'building',
    application: 'Muros cortina de gran altura, fachadas de doble piel',
    priceUSD: 580, pricePerWp: 2.54,
    isCustom: false, color: '#d97706', brand: 'soltech',
  },
  {
    id: 'SOL_LAM3_T0_2300', hiitioId: '', name: 'SOLTECH · ASP-LAM3-T0 (1215x2300mm, 423W)',
    category: 'soltech_laminado',
    description: 'Vidrio laminado BIPV 1215x2300mm, 0% transparencia. Formato gigante de alto rendimiento.',
    pmax: 423, voc: 184.0, isc: 2.65, vmp: 152.0, imp: 2.45,
    efficiencySTC: 15.1, tempCoeffPmax: -0.321,
    lengthMm: 2300, widthMm: 1215, weightKg: 115.0,
    noct: 45, systemLoss: 14, degradationAnnual: 0.40,
    pvgisTechchoice: 'CdTe', pvgisMountingplace: 'building',
    application: 'Integración en muro cortina estructural de grandes dimensiones',
    priceUSD: 720, pricePerWp: 1.70,
    isCustom: false, color: '#d97706', brand: 'soltech',
  },
  {
    id: 'SOL_LAM3_T30_2300', hiitioId: '', name: 'SOLTECH · ASP-LAM3-T30 (1215x2300mm, 296W)',
    category: 'soltech_laminado',
    description: 'Vidrio laminado BIPV 1215x2300mm, 30% transparencia. Máxima expresión e integración arquitectónica.',
    pmax: 296, voc: 184.0, isc: 1.90, vmp: 152.0, imp: 1.72,
    efficiencySTC: 10.6, tempCoeffPmax: -0.321,
    lengthMm: 2300, widthMm: 1215, weightKg: 115.0,
    noct: 45, systemLoss: 14, degradationAnnual: 0.40,
    pvgisTechchoice: 'CdTe', pvgisMountingplace: 'building',
    application: 'Fachadas estructurales acristaladas de oficinas corporativas',
    priceUSD: 780, pricePerWp: 2.64,
    isCustom: false, color: '#d97706', brand: 'soltech',
  },
  // ===== SOLTECH — Vidrio Opaco (ASP-S1) =====
  {
    id: 'SOL_S1_105', hiitioId: '', name: 'SOLTECH · ASP-S1-105 (105W)',
    category: 'soltech_opaco',
    description: 'Vidrio solar opaco BIPV de 105W en formato compacto de 1200x600mm. Ideal para revestimiento exterior.',
    pmax: 105, voc: 116.0, isc: 1.39, vmp: 90.0, imp: 1.17,
    efficiencySTC: 14.6, tempCoeffPmax: -0.321,
    lengthMm: 1200, widthMm: 600, weightKg: 12.0,
    noct: 46, systemLoss: 16, degradationAnnual: 0.45,
    pvgisTechchoice: 'CdTe', pvgisMountingplace: 'building',
    application: 'Spandrel, revestimiento de fachadas ventiladas modulares',
    priceUSD: 190, pricePerWp: 1.81,
    isCustom: false, color: '#d97706', brand: 'soltech',
  },
  {
    id: 'SOL_S1_115', hiitioId: '', name: 'SOLTECH · ASP-S1-115 (115W)',
    category: 'soltech_opaco',
    description: 'Vidrio solar opaco BIPV de 115W en formato compacto 1200x600mm. Eficiencia de 16.0%.',
    pmax: 115, voc: 180.49, isc: 0.918, vmp: 142.0, imp: 0.81,
    efficiencySTC: 16.0, tempCoeffPmax: -0.321,
    lengthMm: 1200, widthMm: 600, weightKg: 12.0,
    noct: 46, systemLoss: 16, degradationAnnual: 0.45,
    pvgisTechchoice: 'CdTe', pvgisMountingplace: 'building',
    application: 'Antepechos de fachada, fachadas ventiladas opacas de alto rendimiento',
    priceUSD: 210, pricePerWp: 1.83,
    isCustom: false, color: '#d97706', brand: 'soltech',
  },
  // ===== SOLTECH — CdTe Transparente (ASP-ST1) =====
  {
    id: 'SOL_ST1_T10', hiitioId: '', name: 'SOLTECH · ASP-ST1-T10 (94W)',
    category: 'soltech_st',
    description: 'Vidrio CdTe compacto 1200x600mm con 10% transparencia y 94W. U=5.13.',
    pmax: 94, voc: 116.0, isc: 1.19, vmp: 90.0, imp: 1.04,
    efficiencySTC: 13.1, tempCoeffPmax: -0.321,
    lengthMm: 1200, widthMm: 600, weightKg: 12.5,
    noct: 45, systemLoss: 14, degradationAnnual: 0.40,
    pvgisTechchoice: 'CdTe', pvgisMountingplace: 'building',
    application: 'Lucernarios industriales, marquesinas, sombreado en atrios',
    priceUSD: 195, pricePerWp: 2.07,
    isCustom: false, color: '#d97706', brand: 'soltech',
  },
  {
    id: 'SOL_ST1_T30', hiitioId: '', name: 'SOLTECH · ASP-ST1-T30 (73W)',
    category: 'soltech_st',
    description: 'Vidrio CdTe compacto 1200x600mm con 30% transparencia y 73W. U=5.13.',
    pmax: 73, voc: 116.0, isc: 0.93, vmp: 90.0, imp: 0.81,
    efficiencySTC: 10.1, tempCoeffPmax: -0.321,
    lengthMm: 1200, widthMm: 600, weightKg: 12.5,
    noct: 45, systemLoss: 14, degradationAnnual: 0.40,
    pvgisTechchoice: 'CdTe', pvgisMountingplace: 'building',
    application: 'Pasamanos solares, barandas de balcones de vidrio, fachadas',
    priceUSD: 205, pricePerWp: 2.81,
    isCustom: false, color: '#d97706', brand: 'soltech',
  },
  {
    id: 'SOL_ST1_T50', hiitioId: '', name: 'SOLTECH · ASP-ST1-T50 (52W)',
    category: 'soltech_st',
    description: 'Vidrio CdTe compacto 1200x600mm con 50% transparencia y 52W. U=5.13.',
    pmax: 52, voc: 116.0, isc: 0.66, vmp: 90.0, imp: 0.58,
    efficiencySTC: 7.2, tempCoeffPmax: -0.321,
    lengthMm: 1200, widthMm: 600, weightKg: 12.5,
    noct: 45, systemLoss: 14, degradationAnnual: 0.40,
    pvgisTechchoice: 'CdTe', pvgisMountingplace: 'building',
    application: 'Ventanas residenciales, marquesinas translucidas para luz natural',
    priceUSD: 215, pricePerWp: 4.13,
    isCustom: false, color: '#d97706', brand: 'soltech',
  },
  {
    id: 'SOL_ST1_T70', hiitioId: '', name: 'SOLTECH · ASP-ST1-T70 (31W)',
    category: 'soltech_st',
    description: 'Vidrio CdTe compacto 1200x600mm con 70% transparencia y 31W. Alta iluminación.',
    pmax: 31, voc: 116.0, isc: 0.40, vmp: 90.0, imp: 0.34,
    efficiencySTC: 4.3, tempCoeffPmax: -0.321,
    lengthMm: 1200, widthMm: 600, weightKg: 12.5,
    noct: 45, systemLoss: 14, degradationAnnual: 0.40,
    pvgisTechchoice: 'CdTe', pvgisMountingplace: 'building',
    application: 'Ventanas y fachadas transparentes con máxima visibilidad',
    priceUSD: 230, pricePerWp: 7.42,
    isCustom: false, color: '#d97706', brand: 'soltech',
  },
  // ===== SOLTECH — Teja Curva CIGS (HW-MQSB) =====
  {
    id: 'SOL_TEJA_V2_BLACK', hiitioId: '', name: 'SOLTECH · HW-MQSB-V2-Black (32W)',
    category: 'soltech_teja',
    description: 'Teja fotovoltaica curva CIGS de 32W, color negro. Clasificación Fuego Clase A, resistencia granizo Nivel 4.',
    pmax: 32, voc: 10.8, isc: 4.10, vmp: 8.9, imp: 3.60,
    efficiencySTC: 8.9, tempCoeffPmax: -0.38,
    lengthMm: 720, widthMm: 500, weightKg: 10.8,
    noct: 47, systemLoss: 16, degradationAnnual: 0.50,
    pvgisTechchoice: 'CIS', pvgisMountingplace: 'building',
    application: 'Cubiertas y techos residenciales de tejas curvas premium',
    priceUSD: 65, pricePerWp: 2.03,
    isCustom: false, color: '#d97706', brand: 'soltech',
  },
  {
    id: 'SOL_TEJA_V2_GREEN', hiitioId: '', name: 'SOLTECH · HW-MQSB-V2-Green (28W)',
    category: 'soltech_teja',
    description: 'Teja fotovoltaica curva CIGS de 28W, color verde. Diseño estético para integración histórica.',
    pmax: 28, voc: 10.5, isc: 3.90, vmp: 8.4, imp: 3.40,
    efficiencySTC: 7.8, tempCoeffPmax: -0.38,
    lengthMm: 720, widthMm: 500, weightKg: 10.5,
    noct: 47, systemLoss: 16, degradationAnnual: 0.50,
    pvgisTechchoice: 'CIS', pvgisMountingplace: 'building',
    application: 'Cubiertas con exigencia de integración paisajística o ecológica',
    priceUSD: 70, pricePerWp: 2.50,
    isCustom: false, color: '#d97706', brand: 'soltech',
  },
  {
    id: 'SOL_TEJA_V2_RED', hiitioId: '', name: 'SOLTECH · HW-MQSB-V2-Red (28W)',
    category: 'soltech_teja',
    description: 'Teja fotovoltaica curva CIGS de 28W, color rojo terracota. Reemplaza tejas de arcilla tradicionales.',
    pmax: 28, voc: 10.5, isc: 3.90, vmp: 8.4, imp: 3.40,
    efficiencySTC: 7.8, tempCoeffPmax: -0.38,
    lengthMm: 720, widthMm: 500, weightKg: 10.5,
    noct: 47, systemLoss: 16, degradationAnnual: 0.50,
    pvgisTechchoice: 'CIS', pvgisMountingplace: 'building',
    application: 'Cubiertas de estilo español/mediterráneo tradicionales',
    priceUSD: 70, pricePerWp: 2.50,
    isCustom: false, color: '#d97706', brand: 'soltech',
  },
  // ===== SOLTECH — NextCity Labs (NCL) =====
  {
    id: 'SOL_NCL_TRANS', hiitioId: '', name: 'SOLTECH · NextCity Labs (CdTe 160W/m²)',
    category: 'soltech_ncl',
    description: 'NextCity Labs BIPV Transparente: Módulo solar de CdTe personalizable hasta 160W/m² (espesor 21mm).',
    pmax: 160, voc: 150.0, isc: 1.50, vmp: 120.0, imp: 1.33,
    efficiencySTC: 16.0, tempCoeffPmax: -0.25,
    lengthMm: 1000, widthMm: 1000, weightKg: 25.0,
    noct: 45, systemLoss: 14, degradationAnnual: 0.40,
    pvgisTechchoice: 'CdTe', pvgisMountingplace: 'building',
    application: 'Proyectos arquitectónicos a medida, vidrios de seguridad solar',
    priceUSD: 450, pricePerWp: 2.81,
    isCustom: false, color: '#d97706', brand: 'soltech',
  },
];

/**
 * Crear una plantilla personalizada basada en una existente
 */
export function createCustomTemplate(baseTech?: PanelTechnology): PanelTechnology {
  const base = baseTech || DEFAULT_PANEL_TECHNOLOGIES[0];
  return {
    ...base,
    id: `custom_${Date.now()}`,
    hiitioId: '',
    name: baseTech ? `${base.name} (Personalizado)` : 'Panel Personalizado',
    description: 'Plantilla personalizada con parámetros editables',
    isCustom: true,
    color: '#8b5cf6',
    brand: 'generic',
  };
}

/**
 * Calcular temperatura de celda
 * Tcell = Tamb + (NOCT - 20) / 800 × G
 */
export function calculateCellTemperature(
  ambientTemp: number,
  noct: number,
  irradiance: number = 800
): number {
  return ambientTemp + ((noct - 20) / 800) * irradiance;
}

/**
 * Calcular producción corregida mensual con parámetros reales del panel
 */
export function calculateCorrectedProduction(
  pvgisMonthlyKwh: number,
  panel: PanelTechnology,
  ambientTempC: number,
  pvgisRefTechchoice: string = 'crystSi',
  yearsFromInstall: number = 0
): {
  correctedKwh: number;
  tempCorrectionFactor: number;
  noctCorrectionFactor: number;
  degradationFactor: number;
  lossAdjustment: number;
  totalCorrectionFactor: number;
} {
  // Coeficientes de referencia PVGIS por tecnología
  const refTempCoeffs: Record<string, number> = {
    'crystSi': -0.35, 'CdTe': -0.28, 'CIS': -0.32, 'Unknown': -0.35,
  };
  const refNOCT = 43; // NOCT referencia PVGIS (rack abierto)
  const refCoeff = refTempCoeffs[pvgisRefTechchoice] || -0.35;

  // Temperatura de celda real vs referencia
  const cellTemp = calculateCellTemperature(ambientTempC, panel.noct);
  const refCellTemp = calculateCellTemperature(ambientTempC, refNOCT);

  // Factor corrección temperatura
  const tempCorrectionFactor = (1 + panel.tempCoeffPmax * (cellTemp - 25) / 100) /
                                (1 + refCoeff * (refCellTemp - 25) / 100);

  // Factor corrección NOCT (mayor NOCT = peor ventilación = más pérdidas)
  const noctCorrectionFactor = panel.noct <= refNOCT ? 1.0 :
    1 - ((panel.noct - refNOCT) * 0.004);

  // Factor degradación
  let degradationFactor = 1.0;
  if (yearsFromInstall > 0) {
    degradationFactor = (1 - 0.02) * // primer año ~2%
      Math.pow(1 - panel.degradationAnnual / 100, Math.max(0, yearsFromInstall - 1));
  }

  // Ajuste pérdidas del sistema (si difiere del 14% estándar PVGIS)
  const lossAdjustment = (1 - panel.systemLoss / 100) / (1 - 14 / 100);

  const totalCorrectionFactor = tempCorrectionFactor * noctCorrectionFactor * degradationFactor * lossAdjustment;
  const correctedKwh = pvgisMonthlyKwh * totalCorrectionFactor;

  return {
    correctedKwh,
    tempCorrectionFactor,
    noctCorrectionFactor,
    degradationFactor,
    lossAdjustment,
    totalCorrectionFactor,
  };
}

export const CATEGORY_LABELS: Record<string, string> = {
  topcon_flex: 'HIITIO — TOPCon Flexible (HCFM)',
  hjt_curtain: 'HIITIO — HJT Curtain Wall (HL-HQB13)',
  hjt_tile: 'HIITIO — HJT Wall Tile (HL-XWB13)',
  cdte_semit: 'HIITIO — CdTe Semitransparente (HC-3CT)',
  cdte_bipv: 'HIITIO — CdTe BIPV Arquitectónico (HC-JL)',
  cigs: 'HIITIO — CIGS Teja Curva',
  einnova_antirreflejo: 'EINNOVA — Antirreflejo (TOPCon N)',
  einnova_bifacial: 'EINNOVA — Bifacial N-Type',
  einnova_teja_bc: 'EINNOVA — Teja BC (Negra/Terracota)',
  einnova_teja_plana: 'EINNOVA — Teja Plana',
  einnova_color_panel: 'EINNOVA — Color Panel Cubierta-Fachada',
  einnova_fachada: 'EINNOVA — Fachada BIPV',
  einnova_flexible: 'EINNOVA — Flexible',
  einnova_agripv: 'EINNOVA — AgriPV Transparente',
  einnova_pavimento: 'EINNOVA — Pavimento Solar',
  einnova_vidrio: 'EINNOVA — Vidrio FV',
  soltech_dvh: 'SOLTECH — DVH Doble Vidrio (ASP-DVH)',
  soltech_laminado: 'SOLTECH — Laminated Vidrio (ASP-LAM3)',
  soltech_opaco: 'SOLTECH — Vidrio Opaco (ASP-S1)',
  soltech_st: 'SOLTECH — CdTe Transparente (ASP-ST1)',
  soltech_teja: 'SOLTECH — Teja Curva CIGS (HW-MQSB)',
  soltech_ncl: 'SOLTECH — NextCity Labs (NCL)',
  generic: 'Tecnologías Genéricas de Referencia',
};

export function getTechnologiesByCategory(techs: PanelTechnology[]): Record<string, PanelTechnology[]> {
  const categories: Record<string, PanelTechnology[]> = {};
  for (const key of Object.keys(CATEGORY_LABELS)) {
    categories[key] = [];
  }
  techs.forEach(t => {
    if (categories[t.category]) {
      categories[t.category].push(t);
    }
  });
  return categories;
}
