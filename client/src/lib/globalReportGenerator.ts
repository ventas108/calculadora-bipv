import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';
import { StoredFacadeReport } from '@/lib/reportTypes';

// Factor de emisión de CO2 para Colombia (kg CO2/kWh)
const CO2_FACTOR_COLOMBIA = 0.126;

interface LocationInfo {
  city: string;
  country: string;
  latitude: number;
  longitude: number;
  elevation: number;
}

export function generateGlobalReport(reports: StoredFacadeReport[], location: LocationInfo): jsPDF {
  const doc = new jsPDF('p', 'mm', 'a4');
  const pageWidth = doc.internal.pageSize.getWidth();
  const pageHeight = doc.internal.pageSize.getHeight();
  const margin = 15;
  let yPosition = 25;

  const checkSpace = (needed: number) => {
    if (yPosition + needed > pageHeight - 20) {
      doc.addPage();
      yPosition = 20;
    }
  };

  const newPage = () => {
    doc.addPage();
    yPosition = 20;
  };

  // ===== PORTADA =====
  doc.setFontSize(22);
  doc.setTextColor(25, 118, 210);
  doc.text('REPORTE GLOBAL COMPARATIVO', pageWidth / 2, yPosition, { align: 'center' });
  yPosition += 10;

  doc.setFontSize(14);
  doc.setTextColor(100, 100, 100);
  doc.text('Analisis Multi-Superficie del Edificio', pageWidth / 2, yPosition, { align: 'center' });
  yPosition += 15;

  doc.setFontSize(11);
  doc.setTextColor(0, 0, 0);
  doc.text(`Ubicacion: ${location.city}, ${location.country}`, margin, yPosition);
  yPosition += 6;
  doc.text(`Coordenadas: ${location.latitude.toFixed(4)} lat, ${location.longitude.toFixed(4)} lng | Elevacion: ${location.elevation} m`, margin, yPosition);
  yPosition += 6;
  doc.text(`Fecha: ${new Date().toLocaleDateString('es-ES')} | Superficies evaluadas: ${reports.length}`, margin, yPosition);
  yPosition += 15;

  // ===== 1. KPIs GLOBALES =====
  doc.setFontSize(14);
  doc.setTextColor(25, 118, 210);
  doc.text('1. INDICADORES GLOBALES DEL EDIFICIO', margin, yPosition);
  yPosition += 10;

  const totalProduction = reports.reduce((s, r) => s + r.data.annualProduction, 0);
  const totalArea = reports.reduce((s, r) => s + r.data.area, 0);
  const totalCapacity = reports.reduce((s, r) => s + (r.data.panelPower * r.data.panelQuantity / 1000), 0);
  const avgCF = reports.length > 0 ? reports.reduce((s, r) => s + r.data.capacityFactor, 0) / reports.length : 0;
  const avgPR = reports.length > 0 ? reports.reduce((s, r) => s + r.data.performanceRatio, 0) / reports.length : 0;
  const avgFS = reports.length > 0 ? reports.reduce((s, r) => s + r.data.annualFS, 0) / reports.length : 0;
  const totalCO2 = totalProduction * CO2_FACTOR_COLOMBIA / 1000;
  const avgPayback = reports.filter(r => r.data.paybackPeriod > 0).length > 0
    ? reports.filter(r => r.data.paybackPeriod > 0).reduce((s, r) => s + r.data.paybackPeriod, 0) / reports.filter(r => r.data.paybackPeriod > 0).length
    : 0;

  const globalKPIs = [
    ['Metrica', 'Valor'],
    ['Produccion Total Edificio', `${totalProduction.toFixed(0)} kWh/ano`],
    ['Capacidad Total Instalada', `${totalCapacity.toFixed(1)} kWp`],
    ['Area Total Evaluada', `${totalArea.toFixed(1)} m2`],
    ['Yield Especifico Global', totalCapacity > 0 ? `${(totalProduction / totalCapacity).toFixed(0)} kWh/kWp/ano` : 'N/A'],
    ['Factor de Capacidad Promedio', `${avgCF.toFixed(1)}%`],
    ['Performance Ratio Promedio', `${avgPR.toFixed(1)}%`],
    ['FS Promedio Ponderado', `${(avgFS * 100).toFixed(1)}%`],
    ['CO2 Evitado Total', `${totalCO2.toFixed(2)} ton/ano`],
    ['Payback Promedio', avgPayback > 0 ? `${avgPayback.toFixed(1)} anos` : 'N/A'],
    ['Superficies Evaluadas', `${reports.length}`],
  ];

  autoTable(doc, {
    startY: yPosition,
    head: [globalKPIs[0]],
    body: globalKPIs.slice(1),
    margin: { left: margin, right: margin },
    theme: 'grid',
    headStyles: { fillColor: [25, 118, 210], textColor: [255, 255, 255] },
    bodyStyles: { textColor: [0, 0, 0] },
    alternateRowStyles: { fillColor: [240, 240, 240] },
  });

  yPosition = (doc as any).lastAutoTable.finalY + 15;

  // ===== 2. TABLA COMPARATIVA =====
  checkSpace(60);
  doc.setFontSize(14);
  doc.setTextColor(25, 118, 210);
  doc.text('2. TABLA COMPARATIVA POR SUPERFICIE', margin, yPosition);
  yPosition += 10;

  const compHead = ['Superficie', 'Area (m2)', 'Tilt', 'Azim', 'Prod. (kWh)', 'CF (%)', 'FS (%)', 'Payback'];
  const compBody = reports.map(r => [
    r.facadeName.length > 18 ? r.facadeName.substring(0, 18) + '...' : r.facadeName,
    r.data.area.toFixed(0),
    `${r.data.tilt.toFixed(0)}°`,
    `${r.data.azimuth.toFixed(0)}°`,
    r.data.annualProduction.toFixed(0),
    r.data.capacityFactor.toFixed(1),
    (r.data.annualFS * 100).toFixed(1),
    r.data.paybackPeriod > 0 ? `${r.data.paybackPeriod.toFixed(1)} a` : 'N/A',
  ]);

  autoTable(doc, {
    startY: yPosition,
    head: [compHead],
    body: compBody,
    margin: { left: margin, right: margin },
    theme: 'grid',
    headStyles: { fillColor: [76, 175, 80], textColor: [255, 255, 255], fontSize: 7 },
    bodyStyles: { textColor: [0, 0, 0], fontSize: 7 },
    alternateRowStyles: { fillColor: [245, 245, 245] },
  });

  yPosition = (doc as any).lastAutoTable.finalY + 15;

  // ===== 3. ANÁLISIS DE SOMBREADO POR SOLSTICIOS =====
  checkSpace(60);
  doc.setFontSize(14);
  doc.setTextColor(25, 118, 210);
  doc.text('3. ANALISIS DE SOMBREADO POR SOLSTICIOS', margin, yPosition);
  yPosition += 10;

  const shadingHead = ['Superficie', 'FS Jun (%)', 'FS Dic (%)', 'FS Prom. Critico (%)', 'Perdida Anual (%)'];
  const shadingBody = reports.map(r => {
    const fsProm = ((r.data.fsJunSolstice + r.data.fsDecSolstice) / 2 * 100).toFixed(1);
    return [
      r.facadeName.length > 20 ? r.facadeName.substring(0, 20) + '...' : r.facadeName,
      (r.data.fsJunSolstice * 100).toFixed(1),
      (r.data.fsDecSolstice * 100).toFixed(1),
      fsProm,
      r.data.annualShadingLoss.toFixed(1),
    ];
  });

  autoTable(doc, {
    startY: yPosition,
    head: [shadingHead],
    body: shadingBody,
    margin: { left: margin, right: margin },
    theme: 'grid',
    headStyles: { fillColor: [255, 152, 0], textColor: [255, 255, 255], fontSize: 8 },
    bodyStyles: { textColor: [0, 0, 0], fontSize: 8 },
    alternateRowStyles: { fillColor: [255, 248, 225] },
  });

  yPosition = (doc as any).lastAutoTable.finalY + 15;

  // ===== 4. ANÁLISIS FINANCIERO COMPARATIVO =====
  checkSpace(60);
  doc.setFontSize(14);
  doc.setTextColor(25, 118, 210);
  doc.text('4. ANALISIS FINANCIERO COMPARATIVO', margin, yPosition);
  yPosition += 10;

  const finHead = ['Superficie', 'Prod. (kWh)', 'Paneles', 'Payback (anos)', 'ROI 25a (%)'];
  const finBody = reports.map(r => [
    r.facadeName.length > 20 ? r.facadeName.substring(0, 20) + '...' : r.facadeName,
    r.data.annualProduction.toFixed(0),
    r.data.panelQuantity.toString(),
    r.data.paybackPeriod > 0 ? r.data.paybackPeriod.toFixed(1) : 'N/A',
    r.data.roi25Year > 0 ? r.data.roi25Year.toFixed(0) : 'N/A',
  ]);

  autoTable(doc, {
    startY: yPosition,
    head: [finHead],
    body: finBody,
    margin: { left: margin, right: margin },
    theme: 'grid',
    headStyles: { fillColor: [156, 39, 176], textColor: [255, 255, 255], fontSize: 8 },
    bodyStyles: { textColor: [0, 0, 0], fontSize: 8 },
    alternateRowStyles: { fillColor: [243, 229, 245] },
  });

  yPosition = (doc as any).lastAutoTable.finalY + 15;

  // ===== 5. RANKING Y RECOMENDACIONES =====
  newPage();
  doc.setFontSize(14);
  doc.setTextColor(25, 118, 210);
  doc.text('5. RANKING Y RECOMENDACIONES', margin, yPosition);
  yPosition += 10;

  // Ranking por producción
  const sortedByProd = [...reports].sort((a, b) => b.data.annualProduction - a.data.annualProduction);
  doc.setFontSize(10);
  doc.setTextColor(0, 0, 0);
  doc.text('Ranking por Produccion Energetica:', margin, yPosition);
  yPosition += 6;

  sortedByProd.forEach((r, i) => {
    checkSpace(8);
    const medal = i === 0 ? '1ro' : i === 1 ? '2do' : i === 2 ? '3ro' : `${i + 1}to`;
    doc.text(`  ${medal}. ${r.facadeName} - ${r.data.annualProduction.toFixed(0)} kWh/ano (CF: ${r.data.capacityFactor.toFixed(1)}%)`, margin, yPosition);
    yPosition += 6;
  });

  yPosition += 8;

  // Ranking por payback
  const sortedByPayback = [...reports].filter(r => r.data.paybackPeriod > 0).sort((a, b) => a.data.paybackPeriod - b.data.paybackPeriod);
  if (sortedByPayback.length > 0) {
    doc.text('Ranking por Retorno de Inversion (menor payback = mejor):', margin, yPosition);
    yPosition += 6;

    sortedByPayback.forEach((r, i) => {
      checkSpace(8);
      const medal = i === 0 ? '1ro' : i === 1 ? '2do' : i === 2 ? '3ro' : `${i + 1}to`;
      doc.text(`  ${medal}. ${r.facadeName} - Payback: ${r.data.paybackPeriod.toFixed(1)} anos`, margin, yPosition);
      yPosition += 6;
    });

    yPosition += 8;
  }

  // Recomendaciones globales
  checkSpace(40);
  doc.setFontSize(11);
  doc.setTextColor(25, 118, 210);
  doc.text('Recomendaciones:', margin, yPosition);
  yPosition += 8;

  doc.setFontSize(9);
  doc.setTextColor(0, 0, 0);

  const recommendations: string[] = [];

  // Mejor superficie
  if (sortedByProd.length > 0) {
    recommendations.push(`- Mejor superficie para instalacion solar: ${sortedByProd[0].facadeName} con ${sortedByProd[0].data.annualProduction.toFixed(0)} kWh/ano y CF de ${sortedByProd[0].data.capacityFactor.toFixed(1)}%.`);
  }

  // Superficie con más sombra
  const worstShading = [...reports].sort((a, b) => a.data.annualFS - b.data.annualFS)[0];
  if (worstShading && worstShading.data.annualFS < 0.90) {
    recommendations.push(`- Superficie con mayor sombreado: ${worstShading.facadeName} (FS = ${(worstShading.data.annualFS * 100).toFixed(1)}%, perdida = ${worstShading.data.annualShadingLoss.toFixed(1)}%). Evaluar mitigacion de obstaculos.`);
  }

  // Producción total
  recommendations.push(`- Produccion total del edificio: ${totalProduction.toFixed(0)} kWh/ano con ${totalCapacity.toFixed(1)} kWp instalados.`);
  recommendations.push(`- Impacto ambiental: ${totalCO2.toFixed(2)} toneladas de CO2 evitadas por ano (equivalente a ${(totalCO2 * 50).toFixed(0)} arboles).`);

  // Payback
  if (avgPayback > 0) {
    recommendations.push(`- Payback promedio del edificio: ${avgPayback.toFixed(1)} anos.`);
    if (avgPayback < 7) {
      recommendations.push('  * Proyecto altamente viable economicamente.');
    } else if (avgPayback < 12) {
      recommendations.push('  * Proyecto viable. Evaluar financiamiento para optimizar flujo de caja.');
    } else {
      recommendations.push('  * Retorno prolongado. Considerar priorizar superficies con menor payback.');
    }
  }

  // Priorización
  if (reports.length > 2) {
    const priority = sortedByPayback.length > 0 ? sortedByPayback.slice(0, Math.ceil(sortedByPayback.length / 2)) : sortedByProd.slice(0, Math.ceil(sortedByProd.length / 2));
    const priorityNames = priority.map(r => r.facadeName).join(', ');
    recommendations.push(`- Prioridad de instalacion (por viabilidad economica): ${priorityNames}.`);
  }

  recommendations.forEach(rec => {
    checkSpace(12);
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
      `Reporte Global Comparativo - Generado: ${new Date().toLocaleString()}`,
      margin,
      pageHeight - 10
    );
  }

  return doc;
}
