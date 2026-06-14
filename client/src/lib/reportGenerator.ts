import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';
import { EPWData } from './epwParser';
import { calculateAnnualProduction, PanelSpecifications, SystemLosses } from './energyProduction';
import { FacadeFullAnalysis } from './facadeShadingAnalysis';

interface ShadingPoint {
  month: string;
  day: number;
  hour: number;
  solarHeight: number;
  solarAzimuth: number;
  obstacle: string;
  shadedArea: number;
  fs: number;
}

interface POAData {
  month: string;
  directPOA: number;
  diffusePOA: number;
  reflectedPOA: number;
  totalPOA: number;
  avgTemp: number;
}

interface EnergyData {
  panelPower: number;
  panelEfficiency: number;
  panelArea: number;
  quantity: number;
  tilt: number;
  azimuth: number;
  annualProduction: number;
  capacityFactor: number;
  performanceRatio: number;
  systemLosses: number;
  paybackPeriod: number;
  roi10Year: number;
  roi25Year: number;
  shadingLoss?: number;
  annualFS?: number;
  shadingSource?: '3d' | 'manual';
  surfaceName?: string;
}

interface MultiFacadeResult {
  facadeName: string;
  azimuth: number;
  tilt: number;
  area: number;
  fsAnnual: number;
  poaAnnual: number;
  productionAC: number;
  specificYield: number;
  performanceRatio: number;
  rank: number;
  // ROI por fachada
  annualSavingsCOP: number; // Ahorro anual en COP
  paybackYears: number; // Período de recuperación en años
  roi25Year: number; // ROI a 25 años (%)
}

export interface MultiFacadeData {
  results: MultiFacadeResult[];
  totalArea: number;
  totalProductionAC: number;
  avgFS: number;
  avgPR: number;
  bestFacade: string;
  panelInfo: string;
  systemCapacity: string;
  // Parámetros financieros del sistema
  systemCostPerWp: number; // Costo por Wp (COP)
  electricityRate: number; // Tarifa eléctrica (COP/kWh)
  totalSystemCost: number; // Costo total del sistema (COP)
}

interface ReportData {
  city: string;
  country: string;
  latitude: number;
  longitude: number;
  elevation: number;
  date: string;
  shadingPoints: ShadingPoint[];
  poaData: POAData[];
  energyData: EnergyData;
  weatherData: EPWData;
  multiFacadeData?: MultiFacadeData;
  facadeAnalysis3D?: FacadeFullAnalysis | null;
}

// Factor de emisión de CO2 para Colombia (kg CO2/kWh)
const CO2_FACTOR_COLOMBIA = 0.126; // Factor SIN Colombia 2023
// Tarifa eléctrica promedio Colombia (COP/kWh) - estrato 4
const ELECTRICITY_RATE_COP = 850;
// TRM aproximada
const TRM = 4200;

export function generateSolarReport(data: ReportData): jsPDF {
  const doc = new jsPDF({
    orientation: 'portrait',
    unit: 'mm',
    format: 'a4',
  });

  const pageWidth = doc.internal.pageSize.getWidth();
  const pageHeight = doc.internal.pageSize.getHeight();
  const margin = 15;
  let yPosition = margin;

  // Función auxiliar para agregar línea separadora
  const addSeparator = () => {
    doc.setDrawColor(200, 200, 200);
    doc.line(margin, yPosition, pageWidth - margin, yPosition);
    yPosition += 5;
  };

  // Función auxiliar para nueva página
  const newPage = () => {
    doc.addPage();
    yPosition = margin;
  };

  // Función auxiliar para verificar espacio disponible
  const checkSpace = (needed: number) => {
    if (yPosition > pageHeight - needed) newPage();
  };

  // ===== AUTO-CÁLCULO DE PRODUCCIÓN =====
  // Si no hay producción calculada pero sí hay datos POA, calculamos automáticamente
  let autoCalcResult: any = null;
  const e = data.energyData;
  const hasPoaData = data.poaData && data.poaData.length > 0;
  const needsAutoCalc = (e.annualProduction || 0) === 0 && hasPoaData;

  if (needsAutoCalc) {
    try {
      const panelSpecs: PanelSpecifications = {
        powerRating: e.panelPower || 400,
        efficiency: (e.panelEfficiency && e.panelEfficiency > 1) ? e.panelEfficiency : 20, // % (20 = 20%)
        temperatureCoefficient: -0.004, // -0.4%/°C relativo (valor típico monocristalino)
        nominalOperatingCellTemperature: 45,
        area: e.panelArea || 2.0,
        quantity: e.quantity || 1,
      };

      const sysLosses: SystemLosses = {
        dcWiring: 2,
        inverterEfficiency: 96,
        acWiring: 1,
        transformerLosses: 0,
        mismatchLosses: 2,
        soilingLosses: 3,
        shadingLosses: 0,
        availabilityLosses: 1,
        iamLosses: 0,
      };

      // Construir datos mensuales POA con temperatura y viento
      const weatherStats = data.weatherData?.weatherData || [];
      const monthlyPOAInput = data.poaData.map((p, idx) => {
        // Calcular temperatura y viento promedio del mes desde weatherData
        const monthRecords = weatherStats.filter(w => w.month === idx + 1);
        const avgTemp = monthRecords.length > 0
          ? monthRecords.reduce((a, w) => a + (w.temperature || 0), 0) / monthRecords.length
          : (p.avgTemp || 25);
        const avgWind = monthRecords.length > 0
          ? monthRecords.reduce((a, w) => a + (w.windSpeed || 0), 0) / monthRecords.length
          : 1.0;

        return {
          month: p.month,
          avgPOA: p.totalPOA || 0,
          avgTemp,
          avgWindSpeed: avgWind,
        };
      });

      // Calcular FS mensuales desde shadingPoints si hay
      let shadingFactors = Array(12).fill(1.0);
      if (data.shadingPoints && data.shadingPoints.length > 0) {
        const monthNames = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
        shadingFactors = monthNames.map(monthName => {
          const monthPoints = data.shadingPoints.filter(p => p.month === monthName);
          if (monthPoints.length === 0) return 1.0;
          return monthPoints.reduce((a, p) => a + (p.fs ?? 1), 0) / monthPoints.length;
        });
      }

      autoCalcResult = calculateAnnualProduction(
        monthlyPOAInput,
        panelSpecs,
        sysLosses,
        shadingFactors
      );
    } catch (err) {
      console.warn('[ReportGen] Auto-cálculo de producción falló:', err);
    }
  }

  // Valores finales (del simulador o auto-calculados)
  const annualProd = (e.annualProduction || 0) > 0 ? e.annualProduction : (autoCalcResult?.totalACEnergy || 0);
  // capacityFactor de calculateAnnualProduction ya viene como % (ej: 15.0 para 15%)
  // e.capacityFactor del UI también viene como % 
  const capFactorPct = (e.capacityFactor || 0) > 0 ? e.capacityFactor : (autoCalcResult?.capacityFactor || 0);
  // performanceRatio de calculateAnnualProduction ya viene como % (ej: 87.3 para 87.3%)
  // e.performanceRatio del UI también viene como %
  const perfRatioPct = (e.performanceRatio || 0) > 0 ? e.performanceRatio : (autoCalcResult?.performanceRatio || 0);
  const specYield = autoCalcResult?.specificYield || (annualProd > 0 ? annualProd / ((e.panelPower || 400) * (e.quantity || 1) / 1000) : 0);
  const monthlyData = autoCalcResult?.monthlyData || [];

  // Cálculos derivados
  const systemCapacityKW = (e.panelPower || 400) * (e.quantity || 1) / 1000;
  const co2Avoided = annualProd * CO2_FACTOR_COLOMBIA / 1000; // toneladas/año
  const annualSavingsCOP = annualProd * ELECTRICITY_RATE_COP;
  const annualSavingsUSD = annualSavingsCOP / TRM;

  // HSP mensual (Horas Sol Pico)
  // totalPOA es el promedio de W/m² sobre TODAS las horas del mes (incluyendo noche=0)
  // HSP_mensual = totalPOA(W/m²) × horasEnMes / 1000 = kWh/m²/mes
  // HSP_diario = totalPOA(W/m²) × 24 / 1000 = kWh/m²/día
  const daysPerMonth = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  const monthlyHSP = data.poaData.map((p, idx) => {
    const days = daysPerMonth[idx] || 30;
    const poaAvg = p.totalPOA || 0; // W/m² promedio sobre todas las horas
    return {
      month: p.month,
      hsp: poaAvg * days * 24 / 1000, // kWh/m²/mes (= HSP mensual)
      poaDaily: poaAvg * 24 / 1000, // kWh/m²/día (= HSP diario)
    };
  });
  const annualHSP = monthlyHSP.reduce((a, m) => a + m.hsp, 0);

  // ===== PORTADA =====
  const isFacadeSpecific = !!data.facadeAnalysis3D;
  const facadeName = data.facadeAnalysis3D?.facadeName || '';

  doc.setFontSize(24);
  doc.setTextColor(25, 118, 210);
  doc.text('REPORTE DE ANALISIS SOLAR', pageWidth / 2, yPosition, { align: 'center' });
  yPosition += 12;

  doc.setFontSize(13);
  doc.setTextColor(100, 100, 100);
  if (isFacadeSpecific) {
    doc.text(`Superficie Evaluada: ${facadeName}`, pageWidth / 2, yPosition, { align: 'center' });
    yPosition += 7;
    doc.setFontSize(11);
    doc.text(`Azimut: ${data.facadeAnalysis3D!.azimuth.toFixed(0)} deg | Inclinacion: ${data.facadeAnalysis3D!.tilt.toFixed(0)} deg | Area: ${data.facadeAnalysis3D!.area.toFixed(1)} m2`, pageWidth / 2, yPosition, { align: 'center' });
  } else {
    const manualSurfaceName = data.energyData.surfaceName || 'Cubierta / Fachada';
    doc.text(`Superficie Evaluada (Manual): ${manualSurfaceName}`, pageWidth / 2, yPosition, { align: 'center' });
    yPosition += 7;
    doc.setFontSize(11);
    const estimatedArea = (data.energyData.panelArea * data.energyData.quantity).toFixed(1);
    doc.text(`Azimut: ${data.energyData.azimuth.toFixed(0)} deg | Inclinacion: ${data.energyData.tilt.toFixed(0)} deg | Area Estimada: ${estimatedArea} m2`, pageWidth / 2, yPosition, { align: 'center' });
  }
  yPosition += 18;

  // Información de ubicación
  doc.setFontSize(11);
  doc.setTextColor(0, 0, 0);
  doc.text(`Ubicacion: ${data.city || 'Sin definir'}, ${data.country || 'Colombia'}`, margin, yPosition);
  yPosition += 7;
  doc.text(`Coordenadas: ${(data.latitude ?? 0).toFixed(4)} N, ${(data.longitude ?? 0).toFixed(4)} O`, margin, yPosition);
  yPosition += 7;
  doc.text(`Elevacion: ${data.elevation || 0} m`, margin, yPosition);
  yPosition += 7;
  doc.text(`Fecha de Reporte: ${data.date}`, margin, yPosition);
  yPosition += 7;
  doc.text(`Capacidad Instalada: ${systemCapacityKW.toFixed(2)} kWp (${e.quantity || 1} x ${e.panelPower || 400}W)`, margin, yPosition);
  yPosition += 18;

  addSeparator();

  // ===== 1. RESUMEN EJECUTIVO =====
  doc.setFontSize(14);
  doc.setTextColor(25, 118, 210);
  doc.text('1. RESUMEN EJECUTIVO', margin, yPosition);
  yPosition += 10;

  doc.setFontSize(10);
  doc.setTextColor(0, 0, 0);

  const avgFS = data.energyData.annualFS !== undefined
    ? data.energyData.annualFS.toFixed(3)
    : data.shadingPoints.length > 0
      ? (data.shadingPoints.reduce((a, p) => a + (p.fs ?? 1), 0) / data.shadingPoints.length).toFixed(3)
      : '1.000 (sin obstaculos)';
  const avgPOA = hasPoaData
    ? `${(data.poaData.reduce((a, p) => a + (p.totalPOA ?? 0), 0) / data.poaData.length).toFixed(0)} W/m2`
    : 'N/A';

  const summaryData = [
    ['Metrica', 'Valor'],
    ['Capacidad Instalada', `${systemCapacityKW.toFixed(2)} kWp`],
    ['Produccion Energetica Anual', annualProd > 0 ? `${annualProd.toFixed(0)} kWh/ano` : 'Sin datos POA'],
    ['Yield Especifico', specYield > 0 ? `${specYield.toFixed(0)} kWh/kWp/ano` : 'N/A'],
    ['Factor de Capacidad', capFactorPct > 0 ? `${capFactorPct.toFixed(1)}%` : 'N/A'],
    ['Ratio de Desempeno (PR)', perfRatioPct > 0 ? `${perfRatioPct.toFixed(1)}%` : 'N/A'],
    ['Factor de Sombreado Promedio', avgFS],
    ['Perdida por Sombreado Ponderada', data.energyData.shadingLoss !== undefined ? `${data.energyData.shadingLoss.toFixed(1)}%` : data.shadingPoints.length > 0 ? `${((1 - data.shadingPoints.reduce((a, p) => a + (p.fs ?? 1), 0) / data.shadingPoints.length) * 100).toFixed(1)}%` : '0.0%'],
    ['Radiacion POA Promedio', avgPOA],
    ['Horas Sol Pico Anuales', annualHSP > 0 ? `${annualHSP.toFixed(0)} h` : 'N/A'],
    ['CO2 Evitado', co2Avoided > 0 ? `${co2Avoided.toFixed(2)} ton/ano` : 'N/A'],
    ['Ahorro Economico Estimado', annualSavingsCOP > 0 ? `$${(annualSavingsCOP / 1000).toFixed(0)} mil COP/ano (~$${annualSavingsUSD.toFixed(0)} USD)` : 'N/A'],
    ['Periodo de Recuperacion', (e.paybackPeriod || 0) > 0 ? `${e.paybackPeriod.toFixed(1)} anos` : 'Requiere datos financieros'],
  ];

  autoTable(doc, {
    startY: yPosition,
    head: [summaryData[0]],
    body: summaryData.slice(1),
    margin: { left: margin, right: margin },
    theme: 'grid',
    headStyles: { fillColor: [25, 118, 210], textColor: [255, 255, 255] },
    bodyStyles: { textColor: [0, 0, 0] },
    alternateRowStyles: { fillColor: [240, 240, 240] },
  });

  yPosition = (doc as any).lastAutoTable.finalY + 10;

  // ===== 2. ANÁLISIS DE SOMBREADO =====
  const hasFacadeShading = isFacadeSpecific && data.energyData.shadingSource !== 'manual' && data.facadeAnalysis3D!.monthlyData && data.facadeAnalysis3D!.monthlyData.length > 0;
  const hasManualShading = data.shadingPoints.length > 0;

  if (hasFacadeShading) {
    // === MODO FACHADA ESPECÍFICA: Solo promedios de solsticios ===
    checkSpace(80);

    doc.setFontSize(14);
    doc.setTextColor(25, 118, 210);
    doc.text('2. ANALISIS DE SOMBREADO', margin, yPosition);
    yPosition += 8;

    doc.setFontSize(10);
    doc.setTextColor(0, 0, 0);
    doc.text(`Superficie: ${facadeName} | Metodo: Analisis geometrico 3D`, margin, yPosition);
    yPosition += 7;

    const fa = data.facadeAnalysis3D!;
    // Solsticios: Jun (mes 6) y Dic (mes 12)
    const junData = fa.monthlyData.find(m => m.month === 6);
    const dicData = fa.monthlyData.find(m => m.month === 12);
    const fsJun = junData ? junData.fsAverage : 1.0;
    const fsDic = dicData ? dicData.fsAverage : 1.0;
    const fsPromSolsticios = (fsJun + fsDic) / 2;

    // Tabla resumen de solsticios
    const solsticeData = [
      ['Parametro', 'Solsticio Junio (21 Jun)', 'Solsticio Diciembre (21 Dic)', 'Promedio Critico'],
      ['FS Promedio', `${(fsJun * 100).toFixed(1)}%`, `${(fsDic * 100).toFixed(1)}%`, `${(fsPromSolsticios * 100).toFixed(1)}%`],
      ['Horas Sol', junData ? `${junData.totalSunHours.toFixed(0)}h` : '--', dicData ? `${dicData.totalSunHours.toFixed(0)}h` : '--', '--'],
      ['Horas Sombra', junData ? `${junData.shadedHours.toFixed(0)}h` : '--', dicData ? `${dicData.shadedHours.toFixed(0)}h` : '--', '--'],
      ['Perdida Sombra', junData ? `${junData.shadingLoss.toFixed(1)}%` : '--', dicData ? `${dicData.shadingLoss.toFixed(1)}%` : '--', `${fa.annualShadingLoss.toFixed(1)}%`],
    ];

    autoTable(doc, {
      startY: yPosition,
      head: [solsticeData[0]],
      body: solsticeData.slice(1),
      margin: { left: margin, right: margin },
      theme: 'grid',
      headStyles: { fillColor: [76, 175, 80], textColor: [255, 255, 255], fontSize: 8 },
      bodyStyles: { textColor: [0, 0, 0], fontSize: 8 },
      alternateRowStyles: { fillColor: [245, 245, 245] },
    });

    yPosition = (doc as any).lastAutoTable.finalY + 7;

    // KPIs de sombreado de la fachada
    doc.setFontSize(9);
    doc.setTextColor(60, 60, 60);
    doc.text(`FS Anual Ponderado: ${(fa.annualFS * 100).toFixed(1)}% | POA con sombra: ${fa.annualPOA.toFixed(0)} kWh/m2/ano | POA sin sombra: ${fa.annualPOANoShading.toFixed(0)} kWh/m2/ano`, margin, yPosition);
    yPosition += 5;
    doc.text(`Perdida anual por sombreado: ${fa.annualShadingLoss.toFixed(1)}% | Area evaluada: ${fa.area.toFixed(1)} m2`, margin, yPosition);
    yPosition += 10;

  } else if (hasManualShading) {
    // === MODO MANUAL: Puntos de análisis genéricos ===
    checkSpace(60);

    doc.setFontSize(14);
    doc.setTextColor(25, 118, 210);
    doc.text('2. ANALISIS DE SOMBREADO', margin, yPosition);
    yPosition += 10;

    doc.setFontSize(10);
    doc.setTextColor(0, 0, 0);
    doc.text(`Total de puntos analizados: ${data.shadingPoints.length}`, margin, yPosition);
    yPosition += 5;

    // FS mensual resumen
    const monthNames = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
    const fsMensual = monthNames.map(m => {
      const pts = data.shadingPoints.filter(p => p.month === m);
      return pts.length > 0 ? pts.reduce((a, p) => a + (p.fs ?? 1), 0) / pts.length : 1.0;
    });

    doc.text('Factores de Sombreado Mensual:', margin, yPosition);
    yPosition += 5;

    const fsTableData = [
      monthNames,
      fsMensual.map(f => `${(f * 100).toFixed(1)}%`),
    ];

    autoTable(doc, {
      startY: yPosition,
      head: [fsTableData[0]],
      body: [fsTableData[1]],
      margin: { left: margin, right: margin },
      theme: 'grid',
      headStyles: { fillColor: [76, 175, 80], textColor: [255, 255, 255], fontSize: 7, halign: 'center' },
      bodyStyles: { textColor: [0, 0, 0], fontSize: 7, halign: 'center' },
    });

    yPosition = (doc as any).lastAutoTable.finalY + 7;

    // Tabla de puntos de análisis (solo solsticios si hay muchos puntos)
    const solsticePoints = data.shadingPoints.filter(p => p.month === 'Jun' || p.month === 'Dic');
    const displayPoints = solsticePoints.length > 0 ? solsticePoints.slice(0, 15) : data.shadingPoints.slice(0, 15);
    const shadingTableData = displayPoints.map(p => [
      p.month || '',
      (p.day ?? '').toString() || '--',
      (p.hour ?? '').toString() || '--',
      (p.solarHeight ?? 0) > 0 ? (p.solarHeight).toFixed(1) : '--',
      (p.solarAzimuth ?? 0) !== 0 ? (p.solarAzimuth).toFixed(1) : '--',
      p.obstacle || '-',
      (p.shadedArea ?? 0).toFixed(1),
      (p.fs ?? 1).toFixed(3),
    ]);

    if (solsticePoints.length > 0) {
      doc.text('Puntos criticos de solsticios (Jun 21 / Dic 21):', margin, yPosition);
      yPosition += 5;
    }

    autoTable(doc, {
      startY: yPosition,
      head: [['Mes', 'Dia', 'Hora', 'Alt. (deg)', 'Azim. (deg)', 'Obstaculo', 'Area Som. (%)', 'FS']],
      body: shadingTableData,
      margin: { left: margin, right: margin },
      theme: 'grid',
      headStyles: { fillColor: [76, 175, 80], textColor: [255, 255, 255], fontSize: 8 },
      bodyStyles: { textColor: [0, 0, 0], fontSize: 8 },
      alternateRowStyles: { fillColor: [245, 245, 245] },
    });

    yPosition = (doc as any).lastAutoTable.finalY + 5;
  } else {
    checkSpace(30);
    doc.setFontSize(14);
    doc.setTextColor(25, 118, 210);
    doc.text('2. ANALISIS DE SOMBREADO', margin, yPosition);
    yPosition += 10;
    doc.setFontSize(10);
    doc.setTextColor(100, 100, 100);
    doc.text('No se han definido puntos de analisis de sombreado. FS = 1.000 (sin obstaculos).', margin, yPosition);
    yPosition += 10;
  }

  // ===== 3. RADIACIÓN SOLAR POA =====
  if (hasPoaData) {
    newPage();

    doc.setFontSize(14);
    doc.setTextColor(25, 118, 210);
    doc.text('3. RADIACION SOLAR (POA) Y HORAS SOL PICO', margin, yPosition);
    yPosition += 10;

    doc.setFontSize(10);
    doc.setTextColor(0, 0, 0);
    doc.text(`Orientacion: Azimut ${(e.azimuth ?? 0).toFixed(1)} deg | Inclinacion ${(e.tilt ?? 0).toFixed(1)} deg | Albedo: 0.2`, margin, yPosition);
    yPosition += 7;

    const poaTableData = data.poaData.map((p, idx) => [
      p.month,
      (p.directPOA ?? 0).toFixed(0),
      (p.diffusePOA ?? 0).toFixed(0),
      (p.reflectedPOA ?? 0).toFixed(0),
      (p.totalPOA ?? 0).toFixed(0),
      (p.avgTemp ?? 0).toFixed(1),
      monthlyHSP[idx] ? monthlyHSP[idx].poaDaily.toFixed(2) : '--',
    ]);

    // Agregar fila TOTAL/PROMEDIO
    const totalDirectPOA = data.poaData.reduce((a, p) => a + (p.directPOA ?? 0), 0);
    const totalDiffusePOA = data.poaData.reduce((a, p) => a + (p.diffusePOA ?? 0), 0);
    const totalReflectedPOA = data.poaData.reduce((a, p) => a + (p.reflectedPOA ?? 0), 0);
    const totalTotalPOA = data.poaData.reduce((a, p) => a + (p.totalPOA ?? 0), 0);
    const avgTempAll = data.poaData.reduce((a, p) => a + (p.avgTemp ?? 0), 0) / data.poaData.length;
    const avgHSPDaily = monthlyHSP.reduce((a, m) => a + m.poaDaily, 0) / monthlyHSP.length;

    poaTableData.push([
      'ANUAL',
      (totalDirectPOA / 12).toFixed(0),
      (totalDiffusePOA / 12).toFixed(0),
      (totalReflectedPOA / 12).toFixed(0),
      (totalTotalPOA / 12).toFixed(0),
      avgTempAll.toFixed(1),
      avgHSPDaily.toFixed(2),
    ]);

    autoTable(doc, {
      startY: yPosition,
      head: [['Mes', 'Directa (W/m2)', 'Difusa (W/m2)', 'Reflejada (W/m2)', 'Total POA (W/m2)', 'Temp. (C)', 'HSP (kWh/m2/dia)']],
      body: poaTableData,
      margin: { left: margin, right: margin },
      theme: 'grid',
      headStyles: { fillColor: [255, 152, 0], textColor: [255, 255, 255], fontSize: 8 },
      bodyStyles: { textColor: [0, 0, 0], fontSize: 8 },
      alternateRowStyles: { fillColor: [255, 248, 225] },
      didParseCell: (hookData: any) => {
        if (hookData.section === 'body' && hookData.row.index === poaTableData.length - 1) {
          hookData.cell.styles.fontStyle = 'bold';
          hookData.cell.styles.fillColor = [255, 235, 180];
        }
      },
    });

    yPosition = (doc as any).lastAutoTable.finalY + 8;

    // Resumen de irradiancia
    doc.setFontSize(9);
    doc.setTextColor(60, 60, 60);
    doc.text(`Irradiancia POA Total Anual: ${annualHSP.toFixed(0)} kWh/m2/ano | HSP Promedio Diario: ${avgHSPDaily.toFixed(2)} kWh/m2/dia | HSP Anual: ${annualHSP.toFixed(0)} h`, margin, yPosition);
    yPosition += 10;
  } else {
    checkSpace(30);
    doc.setFontSize(14);
    doc.setTextColor(25, 118, 210);
    doc.text('3. RADIACION SOLAR (POA)', margin, yPosition);
    yPosition += 10;
    doc.setFontSize(10);
    doc.setTextColor(100, 100, 100);
    doc.text('Datos POA no disponibles. Se calculan automaticamente al cargar un archivo EPW.', margin, yPosition);
    yPosition += 10;
  }

  // ===== 4. PROYECCIONES ENERGÉTICAS =====
  checkSpace(80);

  doc.setFontSize(14);
  doc.setTextColor(25, 118, 210);
  doc.text('4. PROYECCIONES ENERGETICAS', margin, yPosition);
  yPosition += 8;

  doc.setFontSize(9);
  doc.setTextColor(80, 80, 80);
  if (needsAutoCalc && autoCalcResult) {
    doc.text('(Calculado automaticamente a partir de datos POA y configuracion del panel)', margin, yPosition);
  } else if ((e.annualProduction || 0) > 0) {
    doc.text('(Datos del Simulador de Energia)', margin, yPosition);
  }
  yPosition += 8;

  doc.setFontSize(10);
  doc.setTextColor(0, 0, 0);

  const energyTableData = [
    ['Parametro', 'Valor'],
    ['Potencia del Panel', `${e.panelPower || 400} W`],
    ['Eficiencia del Panel', `${(e.panelEfficiency && e.panelEfficiency > 1 ? e.panelEfficiency : 20).toFixed(1)}%`],
    ['Area del Panel', `${(e.panelArea || 2.0).toFixed(2)} m2`],
    ['Cantidad de Paneles', `${e.quantity || 1}`],
    ['Potencia Total Instalada', `${systemCapacityKW.toFixed(2)} kWp`],
    ['Inclinacion', `${(e.tilt ?? 15).toFixed(1)} deg`],
    ['Azimut', `${(e.azimuth ?? 0).toFixed(1)} deg`],
    ['', ''],
    ['Produccion Anual AC', annualProd > 0 ? `${annualProd.toFixed(0)} kWh/ano` : 'Sin datos POA'],
    ['Yield Especifico', specYield > 0 ? `${specYield.toFixed(0)} kWh/kWp/ano` : 'N/A'],
    ['Factor de Capacidad', capFactorPct > 0 ? `${capFactorPct.toFixed(1)}%` : 'N/A'],
    ['Ratio de Desempeno (PR)', perfRatioPct > 0 ? `${perfRatioPct.toFixed(1)}%` : 'N/A'],
    ['Perdidas del Sistema', `${((e.systemLosses || 0.15) * 100).toFixed(1)}%`],
    ['', ''],
    ['CO2 Evitado', co2Avoided > 0 ? `${co2Avoided.toFixed(2)} ton/ano` : 'N/A'],
    ['Ahorro Economico', annualSavingsCOP > 0 ? `$${(annualSavingsCOP / 1000).toFixed(0)} mil COP/ano` : 'N/A'],
  ];

  autoTable(doc, {
    startY: yPosition,
    head: [energyTableData[0]],
    body: energyTableData.slice(1),
    margin: { left: margin, right: margin },
    theme: 'grid',
    headStyles: { fillColor: [156, 39, 176], textColor: [255, 255, 255] },
    bodyStyles: { textColor: [0, 0, 0] },
    alternateRowStyles: { fillColor: [245, 240, 250] },
  });

  yPosition = (doc as any).lastAutoTable.finalY + 10;

  // ===== 4.1 PRODUCCIÓN MENSUAL DESGLOSADA =====
  if (monthlyData && monthlyData.length > 0) {
    checkSpace(80);

    doc.setFontSize(11);
    doc.setTextColor(25, 118, 210);
    doc.text('4.1 Produccion Mensual Desglosada', margin, yPosition);
    yPosition += 7;

    const monthlyTableData = monthlyData.map((m: any) => [
      m.month || '',
      (m.avgPOA ?? 0).toFixed(0),
      (m.cellTemperature ?? 0).toFixed(1),
      (m.dcEnergy ?? 0).toFixed(1),
      (m.energyProduced ?? 0).toFixed(1),
      (m.panelEfficiency ?? 0).toFixed(1),
    ]);

    // Totales
    const totalDC = monthlyData.reduce((a: number, m: any) => a + (m.dcEnergy || 0), 0);
    const totalAC = monthlyData.reduce((a: number, m: any) => a + (m.energyProduced || 0), 0);
    monthlyTableData.push(['TOTAL', '--', '--', totalDC.toFixed(1), totalAC.toFixed(1), '--']);

    autoTable(doc, {
      startY: yPosition,
      head: [['Mes', 'POA Ef. (W/m2)', 'T. Celda (C)', 'E. DC (kWh)', 'E. AC (kWh)', 'Efic. (%)']],
      body: monthlyTableData,
      margin: { left: margin, right: margin },
      theme: 'grid',
      headStyles: { fillColor: [156, 39, 176], textColor: [255, 255, 255], fontSize: 8 },
      bodyStyles: { textColor: [0, 0, 0], fontSize: 8 },
      alternateRowStyles: { fillColor: [248, 240, 255] },
      didParseCell: (hookData: any) => {
        if (hookData.section === 'body' && hookData.row.index === monthlyTableData.length - 1) {
          hookData.cell.styles.fontStyle = 'bold';
          hookData.cell.styles.fillColor = [230, 210, 250];
        }
      },
    });

    yPosition = (doc as any).lastAutoTable.finalY + 10;
  }

  // ===== 5. ANÁLISIS FINANCIERO =====
  if ((e.paybackPeriod || 0) > 0 || (e.roi10Year || 0) > 0) {
    checkSpace(60);

    doc.setFontSize(14);
    doc.setTextColor(25, 118, 210);
    doc.text('5. ANALISIS FINANCIERO', margin, yPosition);
    yPosition += 10;

    doc.setFontSize(10);
    doc.setTextColor(0, 0, 0);

    const financialData = [
      ['Metrica', 'Valor'],
      ['Periodo de Recuperacion (Payback)', (e.paybackPeriod || 0) > 0 ? `${e.paybackPeriod.toFixed(1)} anos` : 'N/A'],
      ['ROI a 10 anos', (e.roi10Year || 0) > 0 ? `${(e.roi10Year * 100).toFixed(1)}%` : 'N/A'],
      ['ROI a 25 anos', (e.roi25Year || 0) > 0 ? `${(e.roi25Year * 100).toFixed(1)}%` : 'N/A'],
      ['Ahorro Anual Estimado', annualSavingsCOP > 0 ? `$${(annualSavingsCOP / 1000).toFixed(0)} mil COP (~$${annualSavingsUSD.toFixed(0)} USD)` : 'N/A'],
    ];

    autoTable(doc, {
      startY: yPosition,
      head: [financialData[0]],
      body: financialData.slice(1),
      margin: { left: margin, right: margin },
      theme: 'grid',
      headStyles: { fillColor: [244, 67, 54], textColor: [255, 255, 255] },
      bodyStyles: { textColor: [0, 0, 0] },
      alternateRowStyles: { fillColor: [255, 245, 245] },
    });

    yPosition = (doc as any).lastAutoTable.finalY + 15;
  }

  // ===== 6. ANÁLISIS MULTI-FACHADA (MODELO 3D) =====
  // Solo se muestra en reportes globales, NO en reportes individuales por fachada
  if (!isFacadeSpecific && data.multiFacadeData && data.multiFacadeData.results.length > 0) {
    newPage();

    doc.setFontSize(14);
    doc.setTextColor(25, 118, 210);
    doc.text('6. ANALISIS COMPARATIVO MULTI-FACHADA (BIPV)', margin, yPosition);
    yPosition += 8;

    doc.setFontSize(9);
    doc.setTextColor(80, 80, 80);
    doc.text('Produccion estimada por superficie del modelo 3D del edificio', margin, yPosition);
    yPosition += 5;
    doc.text(`Panel: ${data.multiFacadeData.panelInfo} | Capacidad: ${data.multiFacadeData.systemCapacity}`, margin, yPosition);
    yPosition += 8;

    // KPIs resumen
    const mf = data.multiFacadeData;
    const totalSavingsBuilding = mf.results.reduce((s, r) => s + (r.annualSavingsCOP || 0), 0);
    const avgPayback = mf.results.length > 0 ? mf.results.reduce((s, r) => s + (r.paybackYears || 0), 0) / mf.results.length : 0;
    const kpiData = [
      ['Metrica', 'Valor'],
      ['Produccion Total Edificio', `${(mf.totalProductionAC ?? 0).toFixed(0)} kWh/ano`],
      ['Area Total Evaluada', `${(mf.totalArea ?? 0).toFixed(1)} m2`],
      ['FS Promedio Ponderado', `${((mf.avgFS ?? 0) * 100).toFixed(1)}%`],
      ['PR Promedio Ponderado', `${((mf.avgPR ?? 0) * 100).toFixed(1)}%`],
      ['Mejor Superficie', mf.bestFacade || 'N/A'],
      ['Superficies Evaluadas', `${mf.results?.length ?? 0}`],
      ['CO2 Evitado (Edificio)', `${((mf.totalProductionAC ?? 0) * CO2_FACTOR_COLOMBIA / 1000).toFixed(2)} ton/ano`],
      ['Ahorro Anual Total (Edificio)', `$${(totalSavingsBuilding / 1000).toFixed(0)} mil COP/ano`],
      ['Payback Promedio', `${avgPayback.toFixed(1)} anos`],
      ['Costo por Wp', `$${(mf.systemCostPerWp || 4500)} COP/Wp`],
      ['Tarifa Electrica', `$${(mf.electricityRate || 850)} COP/kWh`],
    ];

    autoTable(doc, {
      startY: yPosition,
      head: [kpiData[0]],
      body: kpiData.slice(1),
      margin: { left: margin, right: margin },
      theme: 'grid',
      headStyles: { fillColor: [103, 58, 183], textColor: [255, 255, 255] },
      bodyStyles: { textColor: [0, 0, 0] },
      alternateRowStyles: { fillColor: [237, 231, 246] },
    });

    yPosition = (doc as any).lastAutoTable.finalY + 10;

    // Tabla de ranking por superficie
    checkSpace(40);
    doc.setFontSize(11);
    doc.setTextColor(25, 118, 210);
    doc.text('Ranking de Superficies por Produccion', margin, yPosition);
    yPosition += 7;

    const facadeTableHead = [['#', 'Superficie', 'Az/Incl', 'FS', 'Prod AC (kWh)', 'Yield', 'Ahorro (mil COP)', 'Payback (anos)', 'ROI 25a (%)']];
    const facadeTableBody = (mf.results || []).map(r => [
      `${r.rank ?? ''}`,
      r.facadeName || '',
      `${(r.azimuth ?? 0).toFixed(0)} / ${(r.tilt ?? 0).toFixed(0)} deg`,
      `${((r.fsAnnual ?? 1) * 100).toFixed(1)}%`,
      (r.productionAC ?? 0).toFixed(0),
      `${(r.specificYield ?? 0).toFixed(0)}`,
      `$${((r.annualSavingsCOP ?? 0) / 1000).toFixed(0)}`,
      (r.paybackYears ?? 99) < 50 ? (r.paybackYears ?? 0).toFixed(1) : '>50',
      (r.roi25Year ?? 0).toFixed(0),
    ]);

    // Agregar fila TOTAL
    const totalSavings = mf.results.reduce((s, r) => s + (r.annualSavingsCOP || 0), 0);
    const bestPayback = Math.min(...mf.results.map(r => r.paybackYears || 99));
    const avgROI25 = mf.results.length > 0 ? mf.results.reduce((s, r) => s + (r.roi25Year || 0), 0) / mf.results.length : 0;
    facadeTableBody.push([
      '',
      'TOTAL / PROMEDIO',
      '',
      `${((mf.avgFS ?? 0) * 100).toFixed(1)}%`,
      (mf.totalProductionAC ?? 0).toFixed(0),
      '--',
      `$${(totalSavings / 1000).toFixed(0)}`,
      bestPayback < 50 ? bestPayback.toFixed(1) : '>50',
      avgROI25.toFixed(0),
    ]);

    autoTable(doc, {
      startY: yPosition,
      head: facadeTableHead,
      body: facadeTableBody,
      margin: { left: margin, right: margin },
      theme: 'grid',
      headStyles: { fillColor: [103, 58, 183], textColor: [255, 255, 255], fontSize: 7 },
      bodyStyles: { textColor: [0, 0, 0], fontSize: 7 },
      alternateRowStyles: { fillColor: [245, 240, 255] },
      columnStyles: {
        0: { cellWidth: 8 },
        1: { cellWidth: 32 },
        2: { cellWidth: 20 },
        3: { cellWidth: 14 },
        4: { cellWidth: 22 },
        5: { cellWidth: 16 },
        6: { cellWidth: 22 },
        7: { cellWidth: 20 },
        8: { cellWidth: 20 },
      },
      didParseCell: (hookData: any) => {
        if (hookData.section === 'body' && hookData.row.index === facadeTableBody.length - 1) {
          hookData.cell.styles.fontStyle = 'bold';
          hookData.cell.styles.fillColor = [220, 210, 240];
        }
      },
    });

    yPosition = (doc as any).lastAutoTable.finalY + 10;

    // ===== ANÁLISIS DE SENSIBILIDAD FINANCIERA =====
    checkSpace(60);
    doc.setFontSize(11);
    doc.setTextColor(25, 118, 210);
    doc.text('Analisis de Sensibilidad Financiera (Tarifa Electrica +/-20%)', margin, yPosition);
    yPosition += 7;

    const baseRate = mf.electricityRate || ELECTRICITY_RATE_COP;
    const scenarios = [
      { name: 'Pesimista (-20%)', factor: 0.80 },
      { name: 'Base', factor: 1.00 },
      { name: 'Optimista (+20%)', factor: 1.20 },
    ];

    const sensitivityHead = [['Escenario', 'Tarifa (COP/kWh)', 'Ahorro Anual (mil COP)', 'Payback (anos)', 'ROI 25a (%)']];
    const totalProdAC = mf.totalProductionAC || 0;
    const totalSysCost = mf.totalSystemCost || (totalProdAC * baseRate * 5); // fallback
    const sensitivityBody = scenarios.map(sc => {
      const rate = baseRate * sc.factor;
      const annualSav = totalProdAC * rate;
      const payback = annualSav > 0 ? totalSysCost / annualSav : 99;
      const roi25 = totalSysCost > 0 ? ((annualSav * 25 - totalSysCost) / totalSysCost) * 100 : 0;
      return [
        sc.name,
        `$${rate.toFixed(0)}`,
        `$${(annualSav / 1000).toFixed(0)}`,
        payback < 50 ? payback.toFixed(1) : '>50',
        roi25.toFixed(0) + '%',
      ];
    });

    autoTable(doc, {
      startY: yPosition,
      head: sensitivityHead,
      body: sensitivityBody,
      margin: { left: margin, right: margin },
      theme: 'grid',
      headStyles: { fillColor: [56, 142, 60], textColor: [255, 255, 255], fontSize: 8 },
      bodyStyles: { textColor: [0, 0, 0], fontSize: 8 },
      alternateRowStyles: { fillColor: [232, 245, 233] },
      didParseCell: (hookData: any) => {
        // Resaltar fila base
        if (hookData.section === 'body' && hookData.row.index === 1) {
          hookData.cell.styles.fontStyle = 'bold';
          hookData.cell.styles.fillColor = [200, 230, 201];
        }
      },
    });

    yPosition = (doc as any).lastAutoTable.finalY + 8;

    // Nota de sensibilidad
    doc.setFontSize(7);
    doc.setTextColor(120, 120, 120);
    const sensNote = `Nota: El analisis de sensibilidad muestra el impacto de variaciones del +/-20% en la tarifa electrica sobre los indicadores financieros del edificio completo. Tarifa base: $${baseRate.toFixed(0)} COP/kWh. Costo sistema: $${(totalSysCost / 1000000).toFixed(1)}M COP.`;
    const sensNoteLines = doc.splitTextToSize(sensNote, pageWidth - 2 * margin);
    doc.text(sensNoteLines, margin, yPosition);
    yPosition += sensNoteLines.length * 4 + 8;

    // Nota metodológica
    checkSpace(20);
    doc.setFontSize(7);
    doc.setTextColor(120, 120, 120);
    const noteText = `Nota: La produccion se calcula individualmente para cada superficie usando su azimut e inclinacion especificos con el modelo Liu-Jordan isotropico. Los FS se calculan por interseccion de obstaculos con la trayectoria solar mensual. Los parametros financieros (tarifa electrica y costo/Wp) se toman de los valores configurados en el Simulador de Produccion.`;
    const noteLines = doc.splitTextToSize(noteText, pageWidth - 2 * margin);
    doc.text(noteLines, margin, yPosition);
    yPosition += noteLines.length * 4 + 10;
  }

  // ===== 7. DATOS METEOROLÓGICOS =====
  checkSpace(80);

  doc.setFontSize(14);
  doc.setTextColor(25, 118, 210);
  const meteoSectionNum = data.multiFacadeData && data.multiFacadeData.results.length > 0 ? '7' : (((e.paybackPeriod || 0) > 0 || (e.roi10Year || 0) > 0) ? '6' : '5');
  doc.text(`${meteoSectionNum}. DATOS METEOROLOGICOS`, margin, yPosition);
  yPosition += 10;

  doc.setFontSize(10);
  doc.setTextColor(0, 0, 0);

  const weatherStats = data.weatherData?.weatherData || [];
  const avgTemp = weatherStats.length > 0 ? weatherStats.reduce((a, w) => a + (w.temperature || 0), 0) / weatherStats.length : 0;
  const avgHumidity = weatherStats.length > 0 ? weatherStats.reduce((a, w) => a + (w.relativeHumidity || 0), 0) / weatherStats.length : 0;
  const avgWindSpeed = weatherStats.length > 0 ? weatherStats.reduce((a, w) => a + (w.windSpeed || 0), 0) / weatherStats.length : 0;
  const totalGHI = weatherStats.reduce((a, w) => a + (w.globalHorizontalIrradiance || 0), 0);
  const avgDNI = weatherStats.length > 0 ? weatherStats.reduce((a, w) => a + (w.directNormalIrradiance || 0), 0) / weatherStats.length : 0;
  const avgDHI = weatherStats.length > 0 ? weatherStats.reduce((a, w) => a + (w.diffuseHorizontalIrradiance || 0), 0) / weatherStats.length : 0;

  const weatherTableData = [
    ['Parametro', 'Valor'],
    ['Temperatura Promedio Anual', `${avgTemp.toFixed(1)} C`],
    ['Humedad Relativa Promedio', `${avgHumidity.toFixed(1)}%`],
    ['Velocidad del Viento Promedio', `${avgWindSpeed.toFixed(2)} m/s`],
    ['GHI Anual', `${(totalGHI / 1000).toFixed(1)} kWh/m2/ano`],
    ['DNI Promedio Horario', `${avgDNI.toFixed(1)} W/m2`],
    ['DHI Promedio Horario', `${avgDHI.toFixed(1)} W/m2`],
    ['Registros horarios', `${weatherStats.length}`],
    ['Fuente de datos', `Archivo EPW - ${data.city}`],
  ];

  autoTable(doc, {
    startY: yPosition,
    head: [weatherTableData[0]],
    body: weatherTableData.slice(1),
    margin: { left: margin, right: margin },
    theme: 'grid',
    headStyles: { fillColor: [33, 150, 243], textColor: [255, 255, 255] },
    bodyStyles: { textColor: [0, 0, 0] },
    alternateRowStyles: { fillColor: [225, 245, 254] },
  });

  yPosition = (doc as any).lastAutoTable.finalY + 15;

  // ===== 8. RECOMENDACIONES =====
  checkSpace(60);

  doc.setFontSize(14);
  doc.setTextColor(25, 118, 210);
  const recoSectionNum = parseInt(meteoSectionNum) + 1;
  doc.text(`${recoSectionNum}. RECOMENDACIONES`, margin, yPosition);
  yPosition += 10;

  doc.setFontSize(10);
  doc.setTextColor(0, 0, 0);

  const recommendations: string[] = [];

  // Recomendación de sombreado con datos específicos
  if (data.shadingPoints.length > 0) {
    const avgFSVal = data.shadingPoints.reduce((a, p) => a + (p.fs ?? 1), 0) / data.shadingPoints.length;
    const minFS = Math.min(...data.shadingPoints.map(p => p.fs ?? 1));
    const maxFS = Math.max(...data.shadingPoints.map(p => p.fs ?? 1));
    const shadingLossPct = ((1 - avgFSVal) * 100).toFixed(1);
    const energyLostByShading = annualProd > 0 ? (annualProd / avgFSVal * (1 - avgFSVal)).toFixed(0) : '0';

    if (avgFSVal > 0.95) {
      recommendations.push(`- Sombreado: Excelente (FS promedio = ${(avgFSVal * 100).toFixed(1)}%, perdida = ${shadingLossPct}%). El sitio tiene minimo sombreado, ideal para instalacion solar.`);
    } else if (avgFSVal > 0.85) {
      recommendations.push(`- Sombreado: Bueno (FS promedio = ${(avgFSVal * 100).toFixed(1)}%, rango ${(minFS * 100).toFixed(0)}-${(maxFS * 100).toFixed(0)}%). Perdida por sombra: ${shadingLossPct}% (~${energyLostByShading} kWh/ano). Considerar optimizacion de layout.`);
    } else if (avgFSVal > 0.70) {
      recommendations.push(`- Sombreado: Moderado (FS promedio = ${(avgFSVal * 100).toFixed(1)}%, rango ${(minFS * 100).toFixed(0)}-${(maxFS * 100).toFixed(0)}%). Perdida por sombra: ${shadingLossPct}% (~${energyLostByShading} kWh/ano). Se recomienda evaluar poda de arboles o reubicacion de paneles.`);
    } else {
      recommendations.push(`- Sombreado: Critico (FS promedio = ${(avgFSVal * 100).toFixed(1)}%, rango ${(minFS * 100).toFixed(0)}-${(maxFS * 100).toFixed(0)}%). Perdida por sombra: ${shadingLossPct}% (~${energyLostByShading} kWh/ano). Requiere intervencion urgente para viabilidad del proyecto.`);
    }

    // Identificar meses con mayor sombreado
    const MONTH_NAMES_REC = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
    const monthlyFS = MONTH_NAMES_REC.map(m => {
      const pts = data.shadingPoints.filter(p => p.month === m);
      return pts.length > 0 ? pts.reduce((a, p) => a + (p.fs ?? 1), 0) / pts.length : 1.0;
    });
    const worstMonthIdx = monthlyFS.indexOf(Math.min(...monthlyFS));
    const bestMonthIdx = monthlyFS.indexOf(Math.max(...monthlyFS));
    if (monthlyFS[worstMonthIdx] < 0.90) {
      recommendations.push(`- Mes critico de sombreado: ${MONTH_NAMES_REC[worstMonthIdx]} (FS = ${(monthlyFS[worstMonthIdx] * 100).toFixed(1)}%). Mejor mes: ${MONTH_NAMES_REC[bestMonthIdx]} (FS = ${(monthlyFS[bestMonthIdx] * 100).toFixed(1)}%).`);
    }
  } else {
    recommendations.push('- Se recomienda realizar un analisis de sombreado para evaluar la viabilidad del sitio.');
  }

  // Recomendación de orientación con análisis de optimización
  const optimalTilt = Math.abs(data.latitude || 6);
  const currentTilt = e.tilt ?? 15;
  const tiltDiff = Math.abs(currentTilt - optimalTilt);
  recommendations.push(`- Orientacion: Azimut ${(e.azimuth ?? 0).toFixed(1)} deg, Inclinacion ${currentTilt.toFixed(1)} deg.`);
  if (tiltDiff > 10) {
    recommendations.push(`  * Inclinacion actual difiere ${tiltDiff.toFixed(0)} deg de la optima (~${optimalTilt.toFixed(0)} deg para latitud ${(data.latitude ?? 0).toFixed(1)} deg). Ajustar podria mejorar produccion un ${(tiltDiff * 0.3).toFixed(0)}-${(tiltDiff * 0.5).toFixed(0)}%.`);
  } else if (tiltDiff > 5) {
    recommendations.push(`  * Inclinacion cercana a la optima (~${optimalTilt.toFixed(0)} deg). Diferencia de ${tiltDiff.toFixed(0)} deg tiene impacto menor (<3%).`);
  } else {
    recommendations.push(`  * Inclinacion optima para latitud ${(data.latitude ?? 0).toFixed(1)} deg. Configuracion ideal.`);
  }

  // Recomendación de producción con contexto
  if (annualProd > 0) {
    recommendations.push(`- Produccion estimada: ${annualProd.toFixed(0)} kWh/ano (${specYield.toFixed(0)} kWh/kWp/ano).`);
    if (specYield > 1800) {
      recommendations.push('  * Yield excepcional (>1800 kWh/kWp). Condiciones de irradiancia superiores al promedio.');
    } else if (specYield > 1500) {
      recommendations.push('  * Yield excelente (>1500 kWh/kWp). Condiciones muy favorables para energia solar.');
    } else if (specYield > 1200) {
      recommendations.push('  * Yield bueno (>1200 kWh/kWp). Condiciones favorables para energia solar.');
    } else if (specYield > 900) {
      recommendations.push('  * Yield moderado. Considerar optimizacion de orientacion o reduccion de perdidas.');
    } else {
      recommendations.push('  * Yield bajo (<900 kWh/kWp). Evaluar viabilidad economica y alternativas de ubicacion.');
    }

    // Producción mensual: identificar meses de mayor/menor producción
    if (monthlyData && monthlyData.length >= 12) {
      const monthProds = monthlyData.map((m: any) => m.energyProduced || 0);
      const maxProdMonth = monthProds.indexOf(Math.max(...monthProds));
      const minProdMonth = monthProds.indexOf(Math.min(...monthProds));
      const MONTH_FULL = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'];
      recommendations.push(`  * Mayor produccion: ${MONTH_FULL[maxProdMonth]} (${monthProds[maxProdMonth].toFixed(1)} kWh). Menor: ${MONTH_FULL[minProdMonth]} (${monthProds[minProdMonth].toFixed(1)} kWh).`);
    }
  }

  // Recomendación de HSP
  if (annualHSP > 0) {
    const avgDailyHSP = annualHSP / 365;
    recommendations.push(`- Recurso solar: HSP anual = ${annualHSP.toFixed(0)} kWh/m2 (promedio diario = ${avgDailyHSP.toFixed(1)} kWh/m2/dia).`);
    if (avgDailyHSP > 5.5) {
      recommendations.push('  * Recurso solar excelente. Zona de alta irradiancia.');
    } else if (avgDailyHSP > 4.5) {
      recommendations.push('  * Recurso solar bueno. Zona favorable para energia fotovoltaica.');
    } else if (avgDailyHSP > 3.5) {
      recommendations.push('  * Recurso solar moderado. Viable con paneles de alta eficiencia.');
    }
  }

  // Recomendación de PR con diagnóstico
  if (perfRatioPct > 0) {
    if (perfRatioPct > 85) {
      recommendations.push(`- PR = ${perfRatioPct.toFixed(1)}%. Desempeno excelente del sistema. Perdidas totales controladas.`);
    } else if (perfRatioPct > 80) {
      recommendations.push(`- PR = ${perfRatioPct.toFixed(1)}%. Desempeno bueno, dentro de rangos tipicos (80-85%).`);
    } else if (perfRatioPct > 70) {
      recommendations.push(`- PR = ${perfRatioPct.toFixed(1)}%. Desempeno aceptable pero mejorable. Revisar perdidas por temperatura y suciedad.`);
    } else {
      recommendations.push(`- PR = ${perfRatioPct.toFixed(1)}%. Desempeno bajo. Revisar: sombreado parcial, degradacion de paneles, dimensionamiento del inversor.`);
    }
  }

  // Recomendación de Factor de Capacidad
  if (capFactorPct > 0) {
    recommendations.push(`- Factor de Capacidad: ${capFactorPct.toFixed(1)}%.`);
    if (capFactorPct > 20) {
      recommendations.push('  * Excelente aprovechamiento de la capacidad instalada.');
    } else if (capFactorPct > 15) {
      recommendations.push('  * Buen aprovechamiento. Valores tipicos para sistemas bien orientados.');
    } else {
      recommendations.push('  * Bajo aprovechamiento. Considerar optimizar orientacion o reducir perdidas.');
    }
  }

  // Recomendación financiera
  if ((e.paybackPeriod || 0) > 0) {
    const payback = e.paybackPeriod;
    recommendations.push(`- Periodo de recuperacion: ${payback.toFixed(1)} anos.`);
    if (payback < 5) {
      recommendations.push('  * Retorno de inversion rapido. Proyecto altamente rentable.');
    } else if (payback < 8) {
      recommendations.push('  * Retorno moderado. Proyecto viable economicamente.');
    } else if (payback < 12) {
      recommendations.push('  * Retorno lento. Evaluar financiamiento y subsidios disponibles.');
    } else {
      recommendations.push('  * Retorno prolongado. Considerar reducir costos o aumentar autoconsumo.');
    }
  } else if (annualSavingsCOP > 0) {
    recommendations.push(`- Ahorro estimado: $${(annualSavingsCOP / 1000).toFixed(0)} mil COP/ano (~$${annualSavingsUSD.toFixed(0)} USD/ano). Configure costos del sistema para calcular payback.`);
  }

  // Recomendaciones de mantenimiento
  recommendations.push('- Mantenimiento: Realizar inspeccion visual y limpieza cada 6 meses. Verificar conexiones electricas anualmente.');
  if (co2Avoided > 0) {
    recommendations.push(`- Impacto ambiental: ${co2Avoided.toFixed(2)} toneladas de CO2 evitadas por ano (equivalente a ${(co2Avoided * 50).toFixed(0)} arboles plantados).`);
  }

  recommendations.forEach(rec => {
    if (yPosition > pageHeight - 20) newPage();
    const lines = doc.splitTextToSize(rec, pageWidth - 2 * margin);
    doc.text(lines, margin, yPosition);
    yPosition += lines.length * 5 + 2;
  });

  // ===== PIE DE PÁGINA =====
  const totalPages = (doc as any).internal.pages.length - 1;
  for (let i = 1; i <= totalPages; i++) {
    (doc as any).setPage(i);
    doc.setFontSize(8);
    doc.setTextColor(150, 150, 150);
    doc.text(
      `Pagina ${i} de ${totalPages}`,
      pageWidth / 2,
      pageHeight - 10,
      { align: 'center' }
    );
    doc.text(
      `Generado: ${new Date().toLocaleString()}`,
      margin,
      pageHeight - 10
    );
  }

  return doc;
}
