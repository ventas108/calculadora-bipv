/**
 * Shading Crossing Report Section — PDF Generation
 * 
 * Genera secciones PDF con los resultados del cruce Máscara+EPW:
 * 1. Tabla resumen de FS por fachada
 * 2. Tabla detallada de FS por hora y evento
 * 3. Gráfico de distribución horaria de FS (barras)
 * 4. Gráfico de situación del cielo (pie chart)
 * 5. Información del modelo 3D importado
 */

import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import type { CrossingResult, FacadeDefinition } from './shadingMaskCrossing';
import type { EvaluationModel } from './buildingModelImporter';

// ─── Types ───────────────────────────────────────────────────────────────────

export interface ShadingCrossingReportData {
  /** Resultados del cruce Máscara+EPW */
  crossingResults: CrossingResult[];
  /** Fachadas evaluadas */
  facades: FacadeDefinition[];
  /** Modelo 3D importado (opcional) */
  evaluationModel?: EvaluationModel | null;
  /** Ubicación */
  latitude: number;
  longitude: number;
  cityName?: string;
  /** Elevación del sitio */
  elevation?: number;
}

// ─── Helper Functions ────────────────────────────────────────────────────────

interface FacadeSummary {
  name: string;
  azimuth: number;
  tilt: number;
  avgFsGeom: number;
  avgFsClim: number;
  avgFs: number;
  maxFs: number;
  minFs: number;
  hoursEvaluated: number;
  despejado: number;
  parcial: number;
  nublado: number;
  cubierto: number;
}

function computeFacadeSummaries(results: CrossingResult[], facades: FacadeDefinition[]): FacadeSummary[] {
  return facades.map(facade => {
    const facadeResults = results.filter(r => r.facade === facade.name);
    if (facadeResults.length === 0) {
      return {
        name: facade.name,
        azimuth: facade.azimuthNormal,
        tilt: facade.tilt,
        avgFsGeom: 0,
        avgFsClim: 0,
        avgFs: 0,
        maxFs: 0,
        minFs: 0,
        hoursEvaluated: 0,
        despejado: 0,
        parcial: 0,
        nublado: 0,
        cubierto: 0,
      };
    }

    const fsGeomValues = facadeResults.map(r => r.fsGeometrico);
    const fsClimValues = facadeResults.map(r => r.fsClimatico);
    const fsValues = facadeResults.map(r => r.fs);

    return {
      name: facade.name,
      azimuth: facade.azimuthNormal,
      tilt: facade.tilt,
      avgFsGeom: fsGeomValues.reduce((a, b) => a + b, 0) / fsGeomValues.length,
      avgFsClim: fsClimValues.reduce((a, b) => a + b, 0) / fsClimValues.length,
      avgFs: fsValues.reduce((a, b) => a + b, 0) / fsValues.length,
      maxFs: Math.max(...fsValues),
      minFs: Math.min(...fsValues),
      hoursEvaluated: facadeResults.length,
      despejado: facadeResults.filter(r => r.situacion === 'Despejado').length,
      parcial: facadeResults.filter(r => r.situacion === 'Parcial').length,
      nublado: facadeResults.filter(r => r.situacion === 'Nublado').length,
      cubierto: facadeResults.filter(r => r.situacion === 'Cubierto').length,
    };
  });
}

interface HourlyDistribution {
  hour: number;
  facades: { [facadeName: string]: number };
}

function computeHourlyDistribution(results: CrossingResult[], facades: FacadeDefinition[]): HourlyDistribution[] {
  const hours = Array.from(new Set(results.map(r => r.hour))).sort((a, b) => a - b);
  
  return hours.map(hour => {
    const hourResults = results.filter(r => r.hour === hour);
    const facadeAvgs: { [name: string]: number } = {};
    
    facades.forEach(facade => {
      const facadeHourResults = hourResults.filter(r => r.facade === facade.name);
      if (facadeHourResults.length > 0) {
        facadeAvgs[facade.name] = facadeHourResults.reduce((a, r) => a + r.fs, 0) / facadeHourResults.length;
      } else {
        facadeAvgs[facade.name] = 0;
      }
    });

    return { hour, facades: facadeAvgs };
  });
}

// ─── Chart Drawing ───────────────────────────────────────────────────────────

const CHART_COLORS = [
  [59, 130, 246],   // blue
  [239, 68, 68],    // red
  [16, 185, 129],   // green
  [245, 158, 11],   // amber
  [139, 92, 246],   // violet
  [236, 72, 153],   // pink
  [6, 182, 212],    // cyan
  [249, 115, 22],   // orange
];

function drawHourlyBarChart(
  doc: jsPDF,
  x: number,
  y: number,
  width: number,
  height: number,
  hourlyData: HourlyDistribution[],
  facades: FacadeDefinition[],
): void {
  const chartLeft = x + 12;
  const chartRight = x + width - 5;
  const chartTop = y + 5;
  const chartBottom = y + height - 15;
  const chartWidth = chartRight - chartLeft;
  const chartHeight = chartBottom - chartTop;

  // Draw axes
  doc.setDrawColor(100, 100, 100);
  doc.setLineWidth(0.3);
  doc.line(chartLeft, chartBottom, chartRight, chartBottom); // X axis
  doc.line(chartLeft, chartTop, chartLeft, chartBottom); // Y axis

  // Y axis labels (0 to 1)
  doc.setFontSize(6);
  doc.setTextColor(100, 100, 100);
  for (let i = 0; i <= 4; i++) {
    const val = i * 0.25;
    const yPos = chartBottom - (val * chartHeight);
    doc.text(val.toFixed(2), chartLeft - 10, yPos + 1);
    doc.setDrawColor(230, 230, 230);
    doc.setLineWidth(0.1);
    doc.line(chartLeft, yPos, chartRight, yPos);
  }

  // Y axis title
  doc.setFontSize(7);
  doc.setTextColor(60, 60, 60);
  doc.text('FS', x + 2, chartTop + chartHeight / 2, { angle: 90 });

  // Draw bars
  if (hourlyData.length === 0) return;
  
  const numGroups = hourlyData.length;
  const groupWidth = chartWidth / numGroups;
  const barWidth = (groupWidth * 0.7) / facades.length;
  const groupPadding = groupWidth * 0.15;

  hourlyData.forEach((hourData, groupIdx) => {
    const groupX = chartLeft + groupIdx * groupWidth;

    facades.forEach((facade, facadeIdx) => {
      const value = hourData.facades[facade.name] || 0;
      const barHeight = value * chartHeight;
      const barX = groupX + groupPadding + facadeIdx * barWidth;
      const barY = chartBottom - barHeight;

      const color = CHART_COLORS[facadeIdx % CHART_COLORS.length];
      doc.setFillColor(color[0], color[1], color[2]);
      doc.rect(barX, barY, barWidth - 0.5, barHeight, 'F');
    });

    // X axis label
    doc.setFontSize(5.5);
    doc.setTextColor(100, 100, 100);
    const label = `${Math.floor(hourData.hour)}:${(hourData.hour % 1 * 60).toString().padStart(2, '0')}`;
    doc.text(label, groupX + groupWidth / 2, chartBottom + 4, { align: 'center' });
  });

  // X axis title
  doc.setFontSize(7);
  doc.setTextColor(60, 60, 60);
  doc.text('Hora Solar', chartLeft + chartWidth / 2, chartBottom + 11, { align: 'center' });

  // Legend
  const legendX = chartRight - facades.length * 25;
  const legendY = y + 2;
  facades.forEach((facade, idx) => {
    const color = CHART_COLORS[idx % CHART_COLORS.length];
    doc.setFillColor(color[0], color[1], color[2]);
    doc.rect(legendX + idx * 25, legendY, 3, 3, 'F');
    doc.setFontSize(5.5);
    doc.setTextColor(60, 60, 60);
    doc.text(facade.name, legendX + idx * 25 + 4, legendY + 2.5);
  });
}

function drawSkyConditionPieChart(
  doc: jsPDF,
  x: number,
  y: number,
  size: number,
  summary: FacadeSummary,
): void {
  const cx = x + size / 2;
  const cy = y + size / 2;
  const radius = size / 2 - 5;

  const total = summary.despejado + summary.parcial + summary.nublado + summary.cubierto;
  if (total === 0) return;

  const segments = [
    { label: 'Despejado', value: summary.despejado, color: [76, 175, 80] as [number, number, number] },
    { label: 'Parcial', value: summary.parcial, color: [255, 193, 7] as [number, number, number] },
    { label: 'Nublado', value: summary.nublado, color: [255, 152, 0] as [number, number, number] },
    { label: 'Cubierto', value: summary.cubierto, color: [158, 158, 158] as [number, number, number] },
  ].filter(s => s.value > 0);

  let startAngle = -Math.PI / 2;

  segments.forEach(segment => {
    const sweepAngle = (segment.value / total) * 2 * Math.PI;
    const endAngle = startAngle + sweepAngle;

    // Draw pie segment using lines (jsPDF doesn't have native arc fill)
    doc.setFillColor(segment.color[0], segment.color[1], segment.color[2]);
    
    // Create path points for the segment
    const points: [number, number][] = [[cx, cy]];
    const steps = Math.max(10, Math.ceil(sweepAngle * 20));
    for (let i = 0; i <= steps; i++) {
      const angle = startAngle + (sweepAngle * i / steps);
      points.push([cx + radius * Math.cos(angle), cy + radius * Math.sin(angle)]);
    }

    // Draw filled polygon
    if (points.length > 2) {
      const firstPoint = points[0];
      doc.moveTo(firstPoint[0], firstPoint[1]);
      doc.setFillColor(segment.color[0], segment.color[1], segment.color[2]);
      
      // Use triangle fan approach
      for (let i = 1; i < points.length - 1; i++) {
        doc.triangle(
          cx, cy,
          points[i][0], points[i][1],
          points[i + 1][0], points[i + 1][1],
          'F'
        );
      }
    }

    startAngle = endAngle;
  });

  // Legend below
  let legendY = y + size + 2;
  segments.forEach(segment => {
    const pct = ((segment.value / total) * 100).toFixed(0);
    doc.setFillColor(segment.color[0], segment.color[1], segment.color[2]);
    doc.rect(x + 2, legendY, 3, 3, 'F');
    doc.setFontSize(6);
    doc.setTextColor(60, 60, 60);
    doc.text(`${segment.label}: ${pct}%`, x + 7, legendY + 2.5);
    legendY += 5;
  });
}

// ─── Main Export Functions ────────────────────────────────────────────────────

/**
 * Agrega la sección de resultados del cruce Máscara+EPW a un documento jsPDF existente.
 * Retorna la posición Y final después de la sección.
 */
export function addShadingCrossingSectionToDoc(
  doc: jsPDF,
  startY: number,
  sectionNumber: number,
  data: ShadingCrossingReportData,
): number {
  const pageWidth = doc.internal.pageSize.getWidth();
  const pageHeight = doc.internal.pageSize.getHeight();
  const margin = 15;
  let y = startY;

  const checkPageBreak = (needed: number) => {
    if (y + needed > pageHeight - 20) {
      doc.addPage();
      y = margin;
    }
  };

  const sectionTitle = (num: string, title: string) => {
    checkPageBreak(20);
    doc.setFontSize(13);
    doc.setTextColor(25, 118, 210);
    doc.text(`${num}. ${title}`, margin, y);
    y += 8;
    doc.setFontSize(9);
    doc.setTextColor(0, 0, 0);
  };

  const { crossingResults, facades, evaluationModel } = data;
  if (crossingResults.length === 0) return y;

  // ===== SECCIÓN: ANÁLISIS DE SOMBREADO POR FACHADA =====
  sectionTitle(String(sectionNumber), 'ANÁLISIS DE SOMBREADO POR FACHADA (Cruce Máscara × EPW)');

  // Descripción
  doc.setFontSize(8);
  doc.setTextColor(80, 80, 80);
  doc.text(
    'Factores de sombreado calculados mediante el cruce de las máscaras de obstrucción geométrica con datos climáticos EPW.',
    margin, y, { maxWidth: pageWidth - 2 * margin }
  );
  y += 5;
  doc.text(
    `Ubicación: ${data.cityName || ''} (${data.latitude.toFixed(4)}°, ${data.longitude.toFixed(4)}°)${data.elevation ? ` — Elevación: ${data.elevation}m` : ''}`,
    margin, y, { maxWidth: pageWidth - 2 * margin }
  );
  y += 8;

  // ─── Modelo 3D Info ────────────────────────────────────────────────────────
  if (evaluationModel) {
    checkPageBreak(25);
    doc.setFontSize(9);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(100, 50, 150);
    doc.text('Modelo 3D Importado:', margin, y);
    y += 5;
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(8);
    doc.setTextColor(60, 60, 60);
    doc.text(`Archivo: ${evaluationModel.fileName}`, margin + 3, y);
    y += 4;
    doc.text(
      `Dimensiones: ${evaluationModel.dimensions.x.toFixed(1)} × ${evaluationModel.dimensions.y.toFixed(1)} × ${evaluationModel.dimensions.z.toFixed(1)} m`,
      margin + 3, y
    );
    y += 4;
    doc.text(
      `Fachadas detectadas: ${evaluationModel.detectedFacades.length} | Vértices: ${evaluationModel.parseResult.vertices.length} | Caras: ${evaluationModel.parseResult.totalFaces}`,
      margin + 3, y
    );
    y += 7;
  }

  // ─── Tabla Resumen por Fachada ─────────────────────────────────────────────
  const summaries = computeFacadeSummaries(crossingResults, facades);

  checkPageBreak(40);
  doc.setFontSize(10);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(0, 0, 0);
  doc.text('Resumen de Factores de Sombreado por Fachada', margin, y);
  y += 6;
  doc.setFont('helvetica', 'normal');

  const summaryTableBody = summaries.map(s => [
    s.name,
    `${s.azimuth.toFixed(0)}°`,
    `${s.tilt.toFixed(0)}°`,
    s.avgFsGeom.toFixed(3),
    s.avgFsClim.toFixed(3),
    s.avgFs.toFixed(3),
    s.maxFs.toFixed(3),
    s.minFs.toFixed(3),
    String(s.hoursEvaluated),
  ]);

  autoTable(doc, {
    startY: y,
    head: [['Fachada', 'Azimut', 'Incl.', 'FS Geom.', 'FS Clim.', 'FS Comb.', 'FS Máx.', 'FS Mín.', 'Horas']],
    body: summaryTableBody,
    margin: { left: margin, right: margin },
    theme: 'grid',
    headStyles: { fillColor: [100, 50, 150], textColor: [255, 255, 255], fontSize: 7.5 },
    bodyStyles: { textColor: [0, 0, 0], fontSize: 7 },
    alternateRowStyles: { fillColor: [248, 245, 255] },
    columnStyles: {
      0: { fontStyle: 'bold', cellWidth: 22 },
      1: { halign: 'center', cellWidth: 14 },
      2: { halign: 'center', cellWidth: 12 },
      3: { halign: 'center', cellWidth: 16 },
      4: { halign: 'center', cellWidth: 16 },
      5: { halign: 'center', cellWidth: 16 },
      6: { halign: 'center', cellWidth: 14 },
      7: { halign: 'center', cellWidth: 14 },
      8: { halign: 'center', cellWidth: 12 },
    },
    didParseCell: (hookData: any) => {
      // Color-code FS values
      if (hookData.section === 'body' && hookData.column.index >= 3 && hookData.column.index <= 7) {
        const val = parseFloat(hookData.cell.raw as string);
        if (!isNaN(val)) {
          if (val >= 0.7) {
            hookData.cell.styles.textColor = [211, 47, 47]; // red - high shading
          } else if (val >= 0.4) {
            hookData.cell.styles.textColor = [245, 124, 0]; // orange - moderate
          } else {
            hookData.cell.styles.textColor = [46, 125, 50]; // green - low shading
          }
        }
      }
    },
  });
  y = (doc as any).lastAutoTable.finalY + 10;

  // ─── Tabla de Situación del Cielo ──────────────────────────────────────────
  checkPageBreak(35);
  doc.setFontSize(10);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(0, 0, 0);
  doc.text('Distribución de Condiciones del Cielo por Fachada', margin, y);
  y += 6;
  doc.setFont('helvetica', 'normal');

  const skyTableBody = summaries.map(s => {
    const total = s.despejado + s.parcial + s.nublado + s.cubierto;
    return [
      s.name,
      `${s.despejado} (${total > 0 ? ((s.despejado / total) * 100).toFixed(0) : 0}%)`,
      `${s.parcial} (${total > 0 ? ((s.parcial / total) * 100).toFixed(0) : 0}%)`,
      `${s.nublado} (${total > 0 ? ((s.nublado / total) * 100).toFixed(0) : 0}%)`,
      `${s.cubierto} (${total > 0 ? ((s.cubierto / total) * 100).toFixed(0) : 0}%)`,
    ];
  });

  autoTable(doc, {
    startY: y,
    head: [['Fachada', 'Despejado', 'Parcial', 'Nublado', 'Cubierto']],
    body: skyTableBody,
    margin: { left: margin, right: margin },
    theme: 'grid',
    headStyles: { fillColor: [76, 175, 80], textColor: [255, 255, 255], fontSize: 8 },
    bodyStyles: { textColor: [0, 0, 0], fontSize: 7.5 },
    alternateRowStyles: { fillColor: [245, 255, 245] },
    columnStyles: {
      0: { fontStyle: 'bold' },
      1: { halign: 'center' },
      2: { halign: 'center' },
      3: { halign: 'center' },
      4: { halign: 'center' },
    },
  });
  y = (doc as any).lastAutoTable.finalY + 10;

  // ─── Gráfico de Distribución Horaria ───────────────────────────────────────
  checkPageBreak(75);
  doc.setFontSize(10);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(0, 0, 0);
  doc.text('Distribución Horaria del Factor de Sombreado Combinado', margin, y);
  y += 3;
  doc.setFont('helvetica', 'normal');

  const hourlyData = computeHourlyDistribution(crossingResults, facades);
  drawHourlyBarChart(doc, margin, y, pageWidth - 2 * margin, 55, hourlyData, facades);
  y += 60;

  // ─── Pie Charts de Situación del Cielo (una por fachada, max 4) ────────────
  if (summaries.length > 0 && summaries.length <= 4) {
    checkPageBreak(55);
    doc.setFontSize(10);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(0, 0, 0);
    doc.text('Condiciones del Cielo por Fachada', margin, y);
    y += 3;
    doc.setFont('helvetica', 'normal');

    const pieSize = Math.min(35, (pageWidth - 2 * margin) / summaries.length - 5);
    summaries.forEach((summary, idx) => {
      const pieX = margin + idx * (pieSize + 8);
      drawSkyConditionPieChart(doc, pieX, y, pieSize, summary);
      // Facade name below
      doc.setFontSize(6);
      doc.setTextColor(60, 60, 60);
      doc.text(summary.name, pieX + pieSize / 2, y + pieSize + 22, { align: 'center' });
    });
    y += pieSize + 28;
  }

  // ─── Tabla Detallada (primeras 30 filas) ───────────────────────────────────
  checkPageBreak(60);
  doc.setFontSize(10);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(0, 0, 0);
  doc.text('Detalle de Puntos de Análisis (muestra)', margin, y);
  y += 4;
  doc.setFontSize(7);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(100, 100, 100);
  doc.text(`Total de puntos evaluados: ${crossingResults.length}. Se muestran los primeros 30.`, margin, y);
  y += 5;

  const detailRows = crossingResults.slice(0, 30).map(r => [
    r.evento,
    `${r.month} ${r.day}`,
    r.hourStr,
    r.facade,
    r.heightSolar.toFixed(1),
    r.azimuthSolar.toFixed(1),
    r.fsGeometrico.toFixed(3),
    r.fsClimatico.toFixed(3),
    r.fs.toFixed(3),
    r.situacion,
  ]);

  autoTable(doc, {
    startY: y,
    head: [['Evento', 'Fecha', 'Hora', 'Fachada', 'Alt.°', 'Az.°', 'FS Geom', 'FS Clim', 'FS', 'Cielo']],
    body: detailRows,
    margin: { left: margin, right: margin },
    theme: 'grid',
    headStyles: { fillColor: [25, 118, 210], textColor: [255, 255, 255], fontSize: 6.5 },
    bodyStyles: { textColor: [0, 0, 0], fontSize: 6 },
    alternateRowStyles: { fillColor: [245, 248, 255] },
    columnStyles: {
      0: { cellWidth: 22 },
      1: { cellWidth: 14 },
      2: { cellWidth: 10 },
      3: { cellWidth: 18 },
      4: { halign: 'center', cellWidth: 12 },
      5: { halign: 'center', cellWidth: 12 },
      6: { halign: 'center', cellWidth: 14 },
      7: { halign: 'center', cellWidth: 14 },
      8: { halign: 'center', cellWidth: 12 },
      9: { cellWidth: 16 },
    },
    didParseCell: (hookData: any) => {
      if (hookData.section === 'body') {
        // Color FS combinado
        if (hookData.column.index === 8) {
          const val = parseFloat(hookData.cell.raw as string);
          if (!isNaN(val)) {
            if (val >= 0.7) hookData.cell.styles.textColor = [211, 47, 47];
            else if (val >= 0.4) hookData.cell.styles.textColor = [245, 124, 0];
            else hookData.cell.styles.textColor = [46, 125, 50];
          }
        }
        // Color situación del cielo
        if (hookData.column.index === 9) {
          const text = hookData.cell.raw as string;
          if (text === 'Despejado') hookData.cell.styles.textColor = [46, 125, 50];
          else if (text === 'Parcial') hookData.cell.styles.textColor = [245, 193, 7];
          else if (text === 'Nublado') hookData.cell.styles.textColor = [245, 124, 0];
          else if (text === 'Cubierto') hookData.cell.styles.textColor = [158, 158, 158];
        }
      }
    },
  });
  y = (doc as any).lastAutoTable.finalY + 10;

  return y;
}

// ─── Standalone PDF Export ───────────────────────────────────────────────────

/**
 * Genera un PDF independiente con los resultados del cruce Máscara+EPW.
 */
export function generateShadingCrossingReport(data: ShadingCrossingReportData): void {
  const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
  const pageWidth = doc.internal.pageSize.getWidth();
  const margin = 15;
  let y = margin;

  // ===== PORTADA =====
  doc.setFontSize(20);
  doc.setTextColor(100, 50, 150);
  doc.text('INFORME DE ANÁLISIS DE SOMBREADO', pageWidth / 2, y + 15, { align: 'center' });
  y += 28;

  doc.setFontSize(12);
  doc.setTextColor(80, 80, 80);
  doc.text('Cruce Máscara de Obstrucción × Datos Climáticos EPW', pageWidth / 2, y, { align: 'center' });
  y += 15;

  doc.setFontSize(10);
  doc.setTextColor(0, 0, 0);
  if (data.cityName) {
    doc.text(`Ubicación: ${data.cityName}`, margin, y);
    y += 6;
  }
  doc.text(`Coordenadas: ${data.latitude.toFixed(4)}°, ${data.longitude.toFixed(4)}°`, margin, y);
  y += 6;
  if (data.elevation) {
    doc.text(`Elevación: ${data.elevation} m`, margin, y);
    y += 6;
  }
  doc.text(`Fecha del Reporte: ${new Date().toLocaleDateString('es-CO', { year: 'numeric', month: 'long', day: 'numeric' })}`, margin, y);
  y += 6;
  doc.text(`Fachadas evaluadas: ${data.facades.length}`, margin, y);
  y += 6;
  doc.text(`Puntos de análisis: ${data.crossingResults.length}`, margin, y);
  y += 6;

  const events = Array.from(new Set(data.crossingResults.map(r => r.evento)));
  doc.text(`Eventos evaluados: ${events.join(', ')}`, margin, y, { maxWidth: pageWidth - 2 * margin });
  y += 15;

  // Separator
  doc.setDrawColor(200, 200, 200);
  doc.line(margin, y, pageWidth - margin, y);
  y += 10;

  // Add main content section
  y = addShadingCrossingSectionToDoc(doc, y, 1, data);

  // ===== PIE DE PÁGINA =====
  const totalPages = doc.getNumberOfPages();
  for (let i = 1; i <= totalPages; i++) {
    doc.setPage(i);
    doc.setFontSize(7);
    doc.setTextColor(150, 150, 150);
    doc.text(
      `Informe Análisis de Sombreado — ${data.cityName || 'Solar Shading Calculator'} — Página ${i}/${totalPages}`,
      pageWidth / 2,
      doc.internal.pageSize.getHeight() - 8,
      { align: 'center' }
    );
  }

  // Guardar
  const filename = `Analisis_Sombreado_${(data.cityName || 'Solar').replace(/\s+/g, '_')}_${new Date().toISOString().slice(0, 10)}.pdf`;
  doc.save(filename);
}
