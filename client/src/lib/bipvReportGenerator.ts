/**
 * Generador de Reporte PDF — Diagnóstico BIPV
 *
 * Genera un informe profesional en PDF con:
 * 1. Portada con datos del sitio
 * 2. Especificaciones del panel
 * 3. Configuración del sitio
 * 4. Producción esperada mensual (3 modelos)
 * 5. Comparación real vs esperada con PRs
 * 6. Métricas de salud del sistema
 * 7. Diagnóstico y recomendaciones
 */

import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import type { BIPVPanelConfig, BIPVSiteConfig, BIPVMonthlyExpected, BIPVComparisonResult, BIPVAnnualSummary } from './bipvDiagnostic';
import type { PerformanceAlert, DiagnosticCause } from '@shared/performanceDiagnostic';
import { addShadingCrossingSectionToDoc, type ShadingCrossingReportData } from './shadingCrossingReportSection';

export interface BIPVReportData {
  panelConfig: BIPVPanelConfig;
  siteConfig: BIPVSiteConfig;
  monthlyExpected: BIPVMonthlyExpected[];
  annualSummary: BIPVAnnualSummary;
  comparison: BIPVComparisonResult | null;
  performanceAlert: PerformanceAlert | null;
  ghiAnnual: number;
  ambientTemp: number;
  regionName: string;
  hasPVGIS: boolean;
  hasPVWatts: boolean;
  radarImageBase64?: string;
  /** Datos opcionales del cruce Máscara+EPW para incluir en el informe */
  shadingCrossingData?: ShadingCrossingReportData | null;
}

const MONTHS_FULL = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'];

export function generateBIPVReport(data: BIPVReportData): void {
  const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
  const pageWidth = doc.internal.pageSize.getWidth();
  const pageHeight = doc.internal.pageSize.getHeight();
  const margin = 15;
  let y = margin;

  const addSeparator = () => {
    doc.setDrawColor(200, 200, 200);
    doc.line(margin, y, pageWidth - margin, y);
    y += 5;
  };

  const newPage = () => {
    doc.addPage();
    y = margin;
  };

  const checkPageBreak = (needed: number) => {
    if (y + needed > pageHeight - 20) newPage();
  };

  const sectionTitle = (num: number, title: string) => {
    checkPageBreak(20);
    doc.setFontSize(13);
    doc.setTextColor(25, 118, 210);
    doc.text(`${num}. ${title}`, margin, y);
    y += 8;
    doc.setFontSize(9);
    doc.setTextColor(0, 0, 0);
  };

  // ===== PORTADA =====
  doc.setFontSize(22);
  doc.setTextColor(25, 118, 210);
  doc.text('INFORME DE DIAGNÓSTICO BIPV', pageWidth / 2, y + 20, { align: 'center' });
  y += 35;

  doc.setFontSize(12);
  doc.setTextColor(80, 80, 80);
  doc.text('Evaluación de Rendimiento de Sistema Fotovoltaico Integrado', pageWidth / 2, y, { align: 'center' });
  y += 15;

  doc.setFontSize(14);
  doc.setTextColor(0, 0, 0);
  doc.text(data.siteConfig.siteName, pageWidth / 2, y, { align: 'center' });
  y += 20;

  doc.setFontSize(10);
  doc.setTextColor(60, 60, 60);
  doc.text(`Coordenadas: ${data.siteConfig.latitude.toFixed(4)}°, ${data.siteConfig.longitude.toFixed(4)}°`, margin, y);
  y += 6;
  doc.text(`Región: ${data.regionName}`, margin, y);
  y += 6;
  doc.text(`GHI Anual: ${data.ghiAnnual.toFixed(0)} kWh/m²/año`, margin, y);
  y += 6;
  doc.text(`Temperatura Ambiente Promedio: ${data.ambientTemp.toFixed(1)} °C`, margin, y);
  y += 6;
  doc.text(`Fecha del Reporte: ${new Date().toLocaleDateString('es-CO', { year: 'numeric', month: 'long', day: 'numeric' })}`, margin, y);
  y += 6;
  doc.text(`Fuentes de Datos: Mulcue-Llanos${data.hasPVGIS ? ' + PVGIS' : ''}${data.hasPVWatts ? ' + PVWatts' : ''}`, margin, y);
  y += 15;

  addSeparator();
  y += 5;

  // ===== SECCIÓN 1: ESPECIFICACIONES DEL PANEL =====
  sectionTitle(1, 'ESPECIFICACIONES DEL PANEL');

  const panelData = [
    ['Modelo / Tecnología', data.panelConfig.name],
    ['Potencia Nominal (STC)', `${data.panelConfig.powerRating} W`],
    ['Eficiencia', `${data.panelConfig.efficiency.toFixed(1)}%`],
    ['Coef. Temperatura (Pmax)', `${data.panelConfig.tempCoeff}%/°C`],
    ['NOCT', `${data.panelConfig.noct} °C`],
    ['Área del Panel', `${data.panelConfig.area.toFixed(2)} m²`],
    ['Cantidad de Paneles', `${data.panelConfig.quantity}`],
    ['Capacidad Instalada', `${(data.panelConfig.powerRating * data.panelConfig.quantity / 1000).toFixed(2)} kWp`],
    ['Años Instalado', `${data.panelConfig.yearsInstalled}`],
    ['Degradación Anual', `${data.panelConfig.annualDegradation}%/año`],
    ['Factor Degradación Actual', `${(Math.pow(1 - data.panelConfig.annualDegradation / 100, data.panelConfig.yearsInstalled) * 100).toFixed(1)}%`],
  ];

  autoTable(doc, {
    startY: y,
    head: [['Parámetro', 'Valor']],
    body: panelData,
    margin: { left: margin, right: margin },
    theme: 'grid',
    headStyles: { fillColor: [25, 118, 210], textColor: [255, 255, 255], fontSize: 9 },
    bodyStyles: { textColor: [0, 0, 0], fontSize: 8 },
    alternateRowStyles: { fillColor: [245, 245, 245] },
    columnStyles: { 0: { fontStyle: 'bold', cellWidth: 55 } },
  });
  y = (doc as any).lastAutoTable.finalY + 10;

  // ===== SECCIÓN 2: CONFIGURACIÓN DEL SITIO =====
  sectionTitle(2, 'CONFIGURACIÓN DEL SITIO');

  const siteData = [
    ['Nombre del Sitio', data.siteConfig.siteName],
    ['Latitud', `${data.siteConfig.latitude.toFixed(4)}°`],
    ['Longitud', `${data.siteConfig.longitude.toFixed(4)}°`],
    ['Inclinación (Campo)', `${data.siteConfig.tiltField}°`],
    ['Azimut (Campo)', `${data.siteConfig.azimuthField}° (0=Sur)`],
    ['Factor de Sombreado', `${(data.siteConfig.shadowFactor * 100).toFixed(0)}%`],
    ['Tipo de Instalación', data.siteConfig.installationType.replace(/_/g, ' ')],
  ];

  autoTable(doc, {
    startY: y,
    head: [['Parámetro', 'Valor']],
    body: siteData,
    margin: { left: margin, right: margin },
    theme: 'grid',
    headStyles: { fillColor: [56, 142, 60], textColor: [255, 255, 255], fontSize: 9 },
    bodyStyles: { textColor: [0, 0, 0], fontSize: 8 },
    alternateRowStyles: { fillColor: [245, 245, 245] },
    columnStyles: { 0: { fontStyle: 'bold', cellWidth: 55 } },
  });
  y = (doc as any).lastAutoTable.finalY + 10;

  // ===== SECCIÓN 3: PRODUCCIÓN ESPERADA MENSUAL =====
  checkPageBreak(80);
  sectionTitle(3, 'PRODUCCIÓN ESPERADA MENSUAL');

  const expectedHeaders = ['Mes', 'Mulcue (kWh)'];
  if (data.hasPVGIS) expectedHeaders.push('PVGIS (kWh)');
  if (data.hasPVWatts) expectedHeaders.push('PVWatts (kWh)');
  expectedHeaders.push('Promedio (kWh)');

  const expectedBody = data.monthlyExpected.map((m, i) => {
    const row: string[] = [MONTHS_FULL[i], m.mulcue_ac_kWh.toFixed(1)];
    if (data.hasPVGIS) row.push(m.pvgis_ac_kWh?.toFixed(1) ?? '—');
    if (data.hasPVWatts) row.push(m.pvwatts_ac_kWh?.toFixed(1) ?? '—');
    row.push(m.expected_ac_kWh.toFixed(1));
    return row;
  });

  // Fila anual
  const annualRow: string[] = ['TOTAL ANUAL', data.annualSummary.mulcue_annual_kWh.toFixed(0)];
  if (data.hasPVGIS) annualRow.push(data.annualSummary.pvgis_annual_kWh?.toFixed(0) ?? '—');
  if (data.hasPVWatts) annualRow.push(data.annualSummary.pvwatts_annual_kWh?.toFixed(0) ?? '—');
  annualRow.push(data.annualSummary.expected_annual_kWh.toFixed(0));
  expectedBody.push(annualRow);

  autoTable(doc, {
    startY: y,
    head: [expectedHeaders],
    body: expectedBody,
    margin: { left: margin, right: margin },
    theme: 'grid',
    headStyles: { fillColor: [25, 118, 210], textColor: [255, 255, 255], fontSize: 8 },
    bodyStyles: { textColor: [0, 0, 0], fontSize: 7.5 },
    alternateRowStyles: { fillColor: [245, 245, 245] },
    didParseCell: (hookData: any) => {
      // Resaltar fila anual
      if (hookData.row.index === 12 && hookData.section === 'body') {
        hookData.cell.styles.fontStyle = 'bold';
        hookData.cell.styles.fillColor = [220, 235, 252];
      }
    },
  });
  y = (doc as any).lastAutoTable.finalY + 10;

  // ===== SECCIÓN 4: COMPARACIÓN REAL VS ESPERADA =====
  if (data.comparison) {
    checkPageBreak(80);
    sectionTitle(4, 'COMPARACIÓN REAL VS ESPERADA');

    const compHeaders = ['Mes', 'Esperado (kWh)', 'Real (kWh)', 'Δ (kWh)', 'Δ (%)', 'P_m (kWh)', 'PR Conv.', 'PR Corr.'];
    const compBody = data.comparison.monthly.map((m) => [
      m.monthName,
      m.expected_kWh.toFixed(1),
      m.real_kWh?.toFixed(1) ?? '—',
      m.delta_kWh?.toFixed(1) ?? '—',
      m.delta_pct !== null ? `${m.delta_pct.toFixed(1)}%` : '—',
      m.pm_kWh.toFixed(1),
      m.pr_conventional !== null ? `${(m.pr_conventional * 100).toFixed(1)}%` : '—',
      m.pr_corrected !== null ? `${(m.pr_corrected * 100).toFixed(1)}%` : '—',
    ]);

    // Fila anual
    const ann = data.comparison.annual;
    compBody.push([
      'ANUAL',
      ann.expected_kWh.toFixed(0),
      ann.real_kWh?.toFixed(0) ?? '—',
      ann.delta_kWh?.toFixed(0) ?? '—',
      ann.delta_pct !== null ? `${ann.delta_pct.toFixed(1)}%` : '—',
      ann.pm_annual_kWh.toFixed(0),
      ann.pr_conventional !== null ? `${(ann.pr_conventional * 100).toFixed(1)}%` : '—',
      ann.pr_corrected !== null ? `${(ann.pr_corrected * 100).toFixed(1)}%` : '—',
    ]);

    autoTable(doc, {
      startY: y,
      head: [compHeaders],
      body: compBody,
      margin: { left: margin, right: margin },
      theme: 'grid',
      headStyles: { fillColor: [156, 39, 176], textColor: [255, 255, 255], fontSize: 7.5 },
      bodyStyles: { textColor: [0, 0, 0], fontSize: 7 },
      alternateRowStyles: { fillColor: [245, 245, 245] },
      didParseCell: (hookData: any) => {
        // Colorear Δ% según semáforo
        if (hookData.column.index === 4 && hookData.section === 'body') {
          const text = hookData.cell.raw as string;
          const val = parseFloat(text);
          if (!isNaN(val)) {
            const absVal = Math.abs(val);
            if (absVal > 15) {
              hookData.cell.styles.textColor = [211, 47, 47]; // rojo
            } else if (absVal > 5) {
              hookData.cell.styles.textColor = [245, 124, 0]; // naranja
            } else {
              hookData.cell.styles.textColor = [46, 125, 50]; // verde
            }
          }
        }
        // Resaltar fila anual
        if (hookData.row.index === 12 && hookData.section === 'body') {
          hookData.cell.styles.fontStyle = 'bold';
          hookData.cell.styles.fillColor = [240, 225, 245];
        }
      },
    });
    y = (doc as any).lastAutoTable.finalY + 10;

    // ===== SECCIÓN 5: MÉTRICAS DE SALUD =====
    checkPageBreak(50);
    sectionTitle(5, 'MÉTRICAS DE SALUD DEL SISTEMA');

    const healthData = [
      ['Health Score', `${data.comparison.healthScore}/100`, data.comparison.healthStatus.toUpperCase()],
      ['PR Convencional (Anual)', ann.pr_conventional !== null ? `${(ann.pr_conventional * 100).toFixed(1)}%` : 'N/A', ann.pr_conventional !== null ? (ann.pr_conventional >= 0.75 ? 'BUENO' : ann.pr_conventional >= 0.6 ? 'REGULAR' : 'DEFICIENTE') : '—'],
      ['PR Corregido (Anual)', ann.pr_corrected !== null ? `${(ann.pr_corrected * 100).toFixed(1)}%` : 'N/A', ann.pr_corrected !== null ? (ann.pr_corrected >= 0.85 ? 'BUENO' : ann.pr_corrected >= 0.7 ? 'REGULAR' : 'DEFICIENTE') : '—'],
      ['P_m Anual (Prod. por Irradiancia)', `${ann.pm_annual_kWh.toFixed(0)} kWh`, '—'],
      ['Producción Esperada (Promedio Modelos)', `${ann.expected_kWh.toFixed(0)} kWh`, '—'],
      ['Producción Real (Inversor)', ann.real_kWh !== null ? `${ann.real_kWh.toFixed(0)} kWh` : 'N/A', '—'],
      ['Desviación Anual', ann.delta_pct !== null ? `${ann.delta_pct.toFixed(1)}%` : 'N/A', ann.delta_pct !== null ? (Math.abs(ann.delta_pct) <= 5 ? 'NORMAL' : Math.abs(ann.delta_pct) <= 15 ? 'MODERADA' : 'ALTA') : '—'],
      ['Specific Yield Esperado', `${data.annualSummary.expected_specificYield.toFixed(0)} kWh/kWp/año`, '—'],
    ];

    autoTable(doc, {
      startY: y,
      head: [['Métrica', 'Valor', 'Estado']],
      body: healthData,
      margin: { left: margin, right: margin },
      theme: 'grid',
      headStyles: { fillColor: [244, 67, 54], textColor: [255, 255, 255], fontSize: 9 },
      bodyStyles: { textColor: [0, 0, 0], fontSize: 8 },
      alternateRowStyles: { fillColor: [245, 245, 245] },
      columnStyles: { 0: { fontStyle: 'bold', cellWidth: 60 } },
      didParseCell: (hookData: any) => {
        if (hookData.column.index === 2 && hookData.section === 'body') {
          const text = (hookData.cell.raw as string).toUpperCase();
          if (text === 'BUENO' || text === 'NORMAL' || text === 'EXCELENTE') {
            hookData.cell.styles.textColor = [46, 125, 50];
          } else if (text === 'REGULAR' || text === 'MODERADA') {
            hookData.cell.styles.textColor = [245, 124, 0];
          } else if (text === 'DEFICIENTE' || text === 'ALTA' || text === 'CRITICO') {
            hookData.cell.styles.textColor = [211, 47, 47];
          }
        }
      },
    });
    y = (doc as any).lastAutoTable.finalY + 10;
  }

  // ===== SECCIÓN RADAR: GRÁFICO DE PRODUCCIÓN MENSUAL =====
  if (data.radarImageBase64) {
    checkPageBreak(130);
    const radarSectionNum = data.comparison ? 6 : 4;
    sectionTitle(radarSectionNum, 'GRÁFICO RADAR — PATRÓN ESTACIONAL DE PRODUCCIÓN');

    doc.setFontSize(8);
    doc.setTextColor(100, 100, 100);
    doc.text('Valores normalizados (% del máximo mensual). Identifique meses donde la producción real se aleja de las fuentes esperadas.', margin, y);
    y += 6;

    // Insertar imagen del radar centrada
    const imgWidth = 140;
    const imgHeight = 110;
    const imgX = (pageWidth - imgWidth) / 2;
    doc.addImage(data.radarImageBase64, 'PNG', imgX, y, imgWidth, imgHeight);
    y += imgHeight + 10;
  }

  // ===== SECCIÓN: ANÁLISIS DE SOMBREADO POR FACHADA (si hay datos del cruce) =====
  let shadingSectionOffset = 0;
  if (data.shadingCrossingData && data.shadingCrossingData.crossingResults.length > 0) {
    const shadingSectionNum = data.comparison ? (data.radarImageBase64 ? 7 : 6) : (data.radarImageBase64 ? 5 : 4);
    y = addShadingCrossingSectionToDoc(doc, y, shadingSectionNum, data.shadingCrossingData);
    shadingSectionOffset = 1;
  }

  // ===== SECCIÓN: DIAGNÓSTICO Y RECOMENDACIONES =====
  checkPageBreak(60);
  const sectionNum = (data.comparison ? (data.radarImageBase64 ? 7 : 6) : (data.radarImageBase64 ? 5 : 4)) + shadingSectionOffset;
  sectionTitle(sectionNum, 'DIAGNÓSTICO Y RECOMENDACIONES');

  if (data.performanceAlert) {
    doc.setFontSize(9);
    doc.setTextColor(0, 0, 0);

    doc.setFont('helvetica', 'bold');
    doc.text(`Nivel de Alerta: ${data.performanceAlert.severity.toUpperCase()}`, margin, y);
    y += 6;
    doc.setFont('helvetica', 'normal');
    doc.text(`Diagnóstico: ${data.performanceAlert.message}`, margin, y, { maxWidth: pageWidth - 2 * margin });
    y += Math.ceil(doc.getTextWidth(data.performanceAlert.message) / (pageWidth - 2 * margin)) * 5 + 4;

    if (data.performanceAlert.causes && data.performanceAlert.causes.length > 0) {
      doc.setFont('helvetica', 'bold');
      doc.text('Causas Probables:', margin, y);
      y += 5;
      doc.setFont('helvetica', 'normal');
      data.performanceAlert.causes.forEach((cause: DiagnosticCause) => {
        checkPageBreak(8);
        doc.text(`• ${cause.name} (${(cause.probability * 100).toFixed(0)}%): ${cause.description}`, margin + 3, y, { maxWidth: pageWidth - 2 * margin - 3 });
        const lines = Math.ceil(doc.getTextWidth(`• ${cause.name} (${(cause.probability * 100).toFixed(0)}%): ${cause.description}`) / (pageWidth - 2 * margin - 3));
        y += lines * 4 + 2;
      });
      y += 3;
    }

    // Recomendaciones extraídas de las causas
    const recs = data.performanceAlert.causes.filter((c: DiagnosticCause) => c.recommendation).map((c: DiagnosticCause) => c.recommendation);
    if (recs.length > 0) {
      doc.setFont('helvetica', 'bold');
      doc.text('Recomendaciones de Mantenimiento:', margin, y);
      y += 5;
      doc.setFont('helvetica', 'normal');
      recs.forEach((rec: string) => {
        checkPageBreak(8);
        doc.text(`• ${rec}`, margin + 3, y, { maxWidth: pageWidth - 2 * margin - 3 });
        y += 5;
      });
      y += 3;
    }
  } else {
    // Recomendaciones genéricas cuando no hay diagnóstico
    doc.setFontSize(9);
    doc.setTextColor(0, 0, 0);

    const genericRecs = [
      'Inspección visual mensual de paneles (suciedad, grietas, decoloración)',
      'Verificar conexiones eléctricas y apriete de terminales cada 6 meses',
      'Monitorear producción diaria del inversor vs producción esperada',
      'Limpieza de paneles según condiciones locales (polvo, contaminación)',
      'Revisión anual de estructura de montaje y anclajes',
      'Verificar que no hayan aparecido nuevas fuentes de sombra',
      'Comparar PR real vs PR esperado mensualmente para detectar degradación',
      'Mantener registro fotográfico del estado de los paneles',
    ];

    doc.setFont('helvetica', 'bold');
    doc.text('Recomendaciones Generales de Mantenimiento:', margin, y);
    y += 6;
    doc.setFont('helvetica', 'normal');
    genericRecs.forEach((rec) => {
      checkPageBreak(8);
      doc.text(`• ${rec}`, margin + 3, y, { maxWidth: pageWidth - 2 * margin - 3 });
      y += 5;
    });
  }

  // ===== SECCIÓN: FÓRMULAS Y REFERENCIAS =====
  checkPageBreak(50);
  const formulaSection = sectionNum + 1;
  sectionTitle(formulaSection, 'FÓRMULAS Y REFERENCIAS');

  doc.setFontSize(8);
  doc.setTextColor(60, 60, 60);

  const formulas = [
    'PR Convencional = E_inversor / P_m',
    'P_m = P_ref × N_paneles × (G / G_ref)   [G_ref = 1000 W/m²]',
    'PR Corregido = E_inversor / E_esperada   [E_esperada = promedio(Mulcue, PVGIS, PVWatts)]',
    'T_cell = T_amb + (NOCT - 20) × G / 800',
    'P_esperada = P_STC × (1 + γ × (T_cell - 25)) × (G / G_ref) × FS × FI',
    '',
    'Referencias:',
    '• IEC 61724-1:2021 — Photovoltaic system performance monitoring',
    '• Mulcue-Llanos — Modelo colombiano de producción fotovoltaica (U. Nacional)',
    '• PVGIS — Photovoltaic Geographical Information System (JRC, European Commission)',
    '• PVWatts v8 — National Renewable Energy Laboratory (NREL)',
  ];

  formulas.forEach((line) => {
    checkPageBreak(6);
    doc.text(line, margin, y);
    y += 4.5;
  });

  // ===== PIE DE PÁGINA =====
  const totalPages = doc.getNumberOfPages();
  for (let i = 1; i <= totalPages; i++) {
    doc.setPage(i);
    doc.setFontSize(7);
    doc.setTextColor(150, 150, 150);
    doc.text(`Informe Diagnóstico BIPV — ${data.siteConfig.siteName} — Página ${i}/${totalPages}`, pageWidth / 2, pageHeight - 8, { align: 'center' });
  }

  // Guardar
  const filename = `Diagnostico_BIPV_${data.siteConfig.siteName.replace(/\s+/g, '_')}_${new Date().toISOString().slice(0, 10)}.pdf`;
  doc.save(filename);
}
