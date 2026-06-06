import { describe, it, expect } from 'vitest';

// Test the FieldMeasurementRecord interface and CSV export logic
// Since the hook uses React state + localStorage, we test the pure logic functions

interface FieldMeasurementRecord {
  id: string;
  timestamp: number;
  label: string;
  ghi: number;
  tempAmbient: number;
  tempCell: number;
  tempCellManual: boolean;
  pExp: number;
  pExpTotal: number;
  prMulcue: number;
  tempLoss: number;
  panelName: string;
  panelPower: number;
  panelQuantity: number;
  noct: number;
  tempCoeff: number;
  latitude: number;
  longitude: number;
  cityName: string;
}

// Replicate the CSV export logic from the hook
function exportCSV(records: FieldMeasurementRecord[]): string {
  if (records.length === 0) return '';

  const headers = [
    'Fecha', 'Hora', 'Etiqueta',
    'GHI (W/m²)', 'T_amb (°C)', 'T_cell (°C)', 'T_cell Manual',
    'P_exp (W)', 'P_exp Total (kW)', 'PR Mulcue (%)', 'Pérdida T° (%)',
    'Panel', 'P_nom (W)', 'Cantidad', 'NOCT (°C)', 'γ (%/°C)',
    'Latitud', 'Longitud', 'Ciudad',
  ];

  const rows = records.map(r => {
    const date = new Date(r.timestamp);
    return [
      date.toLocaleDateString('es-CO'),
      date.toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
      `"${r.label.replace(/"/g, '""')}"`,
      r.ghi.toFixed(1),
      r.tempAmbient.toFixed(1),
      r.tempCell.toFixed(1),
      r.tempCellManual ? 'Sí' : 'No',
      r.pExp.toFixed(1),
      r.pExpTotal.toFixed(3),
      (r.prMulcue * 100).toFixed(1),
      ((1 - r.tempLoss) * 100).toFixed(1),
      `"${r.panelName}"`,
      r.panelPower.toString(),
      r.panelQuantity.toString(),
      r.noct.toString(),
      r.tempCoeff.toFixed(3),
      r.latitude.toFixed(4),
      r.longitude.toFixed(4),
      `"${r.cityName}"`,
    ].join(',');
  });

  return [headers.join(','), ...rows].join('\n');
}

// Replicate the groupByDay logic
function groupByDay(records: FieldMeasurementRecord[]): Record<string, FieldMeasurementRecord[]> {
  const groups: Record<string, FieldMeasurementRecord[]> = {};
  records.forEach(r => {
    const dateKey = new Date(r.timestamp).toLocaleDateString('es-CO');
    if (!groups[dateKey]) groups[dateKey] = [];
    groups[dateKey].push(r);
  });
  Object.values(groups).forEach(group => group.sort((a, b) => a.timestamp - b.timestamp));
  return groups;
}

function createMockRecord(overrides: Partial<FieldMeasurementRecord> = {}): FieldMeasurementRecord {
  return {
    id: `fm_${Date.now()}_test`,
    timestamp: Date.now(),
    label: 'Test medición',
    ghi: 800,
    tempAmbient: 28,
    tempCell: 45.2,
    tempCellManual: false,
    pExp: 312.5,
    pExpTotal: 3.125,
    prMulcue: 0.82,
    tempLoss: 0.89,
    panelName: 'Test Panel',
    panelPower: 400,
    panelQuantity: 10,
    noct: 45,
    tempCoeff: -0.35,
    latitude: 6.25,
    longitude: -75.56,
    cityName: 'Medellín',
    ...overrides,
  };
}

describe('FieldMeasurementRecord', () => {
  it('should create a valid record with all required fields', () => {
    const record = createMockRecord();
    expect(record.id).toBeDefined();
    expect(record.timestamp).toBeGreaterThan(0);
    expect(record.ghi).toBe(800);
    expect(record.tempAmbient).toBe(28);
    expect(record.tempCell).toBe(45.2);
    expect(record.pExp).toBe(312.5);
    expect(record.prMulcue).toBe(0.82);
    expect(record.tempLoss).toBe(0.89);
  });

  it('should distinguish between manual and auto T_cell', () => {
    const autoRecord = createMockRecord({ tempCellManual: false });
    const manualRecord = createMockRecord({ tempCellManual: true, tempCell: 52.0 });
    expect(autoRecord.tempCellManual).toBe(false);
    expect(manualRecord.tempCellManual).toBe(true);
    expect(manualRecord.tempCell).toBe(52.0);
  });

  it('should calculate P_exp delta vs STC correctly', () => {
    const record = createMockRecord({ pExp: 320, panelPower: 400 });
    const deltaPercent = ((record.pExp / record.panelPower) - 1) * 100;
    expect(deltaPercent).toBeCloseTo(-20, 0);
  });

  it('should calculate temp loss percentage correctly', () => {
    const record = createMockRecord({ tempLoss: 0.89 });
    const lossPercent = (1 - record.tempLoss) * 100;
    expect(lossPercent).toBeCloseTo(11, 0);
  });
});

describe('CSV Export', () => {
  it('should return empty string for empty records', () => {
    expect(exportCSV([])).toBe('');
  });

  it('should generate valid CSV with headers and data', () => {
    const records = [createMockRecord()];
    const csv = exportCSV(records);
    const lines = csv.split('\n');
    expect(lines.length).toBe(2); // header + 1 data row
    expect(lines[0]).toContain('Fecha');
    expect(lines[0]).toContain('GHI (W/m²)');
    expect(lines[0]).toContain('P_exp (W)');
    expect(lines[0]).toContain('PR Mulcue (%)');
  });

  it('should export correct values in CSV', () => {
    const record = createMockRecord({
      ghi: 950,
      tempAmbient: 32.5,
      tempCell: 55.3,
      pExp: 285.7,
      pExpTotal: 2.857,
      prMulcue: 0.78,
      tempLoss: 0.85,
    });
    const csv = exportCSV([record]);
    const dataLine = csv.split('\n')[1];
    expect(dataLine).toContain('950.0');
    expect(dataLine).toContain('32.5');
    expect(dataLine).toContain('55.3');
    expect(dataLine).toContain('285.7');
    expect(dataLine).toContain('2.857');
    expect(dataLine).toContain('78.0'); // PR %
    expect(dataLine).toContain('15.0'); // temp loss %
  });

  it('should handle labels with quotes in CSV', () => {
    const record = createMockRecord({ label: 'Medición con "comillas"' });
    const csv = exportCSV([record]);
    const dataLine = csv.split('\n')[1];
    expect(dataLine).toContain('"Medición con ""comillas"""');
  });

  it('should export multiple records in chronological order', () => {
    const records = [
      createMockRecord({ timestamp: 1000, ghi: 200, label: 'amanecer' }),
      createMockRecord({ timestamp: 2000, ghi: 800, label: 'mediodía' }),
      createMockRecord({ timestamp: 3000, ghi: 400, label: 'tarde' }),
    ];
    const csv = exportCSV(records);
    const lines = csv.split('\n');
    expect(lines.length).toBe(4); // header + 3 rows
    expect(lines[1]).toContain('200.0');
    expect(lines[2]).toContain('800.0');
    expect(lines[3]).toContain('400.0');
  });

  it('should mark manual T_cell as Sí', () => {
    const record = createMockRecord({ tempCellManual: true });
    const csv = exportCSV([record]);
    expect(csv.split('\n')[1]).toContain('Sí');
  });

  it('should mark auto T_cell as No', () => {
    const record = createMockRecord({ tempCellManual: false });
    const csv = exportCSV([record]);
    expect(csv.split('\n')[1]).toContain('No');
  });
});

describe('Group by Day', () => {
  it('should group records by date', () => {
    // Create records on same day
    const baseTime = new Date('2025-06-15T08:00:00').getTime();
    const records = [
      createMockRecord({ id: '1', timestamp: baseTime, ghi: 300 }),
      createMockRecord({ id: '2', timestamp: baseTime + 3600000, ghi: 600 }), // +1h
      createMockRecord({ id: '3', timestamp: baseTime + 7200000, ghi: 900 }), // +2h
    ];
    const groups = groupByDay(records);
    const dayKeys = Object.keys(groups);
    expect(dayKeys.length).toBe(1);
    expect(groups[dayKeys[0]].length).toBe(3);
  });

  it('should sort records within a day by timestamp ascending', () => {
    const baseTime = new Date('2025-06-15T08:00:00').getTime();
    const records = [
      createMockRecord({ id: '3', timestamp: baseTime + 7200000, ghi: 900 }),
      createMockRecord({ id: '1', timestamp: baseTime, ghi: 300 }),
      createMockRecord({ id: '2', timestamp: baseTime + 3600000, ghi: 600 }),
    ];
    const groups = groupByDay(records);
    const dayRecords = Object.values(groups)[0];
    expect(dayRecords[0].ghi).toBe(300);
    expect(dayRecords[1].ghi).toBe(600);
    expect(dayRecords[2].ghi).toBe(900);
  });

  it('should separate records from different days', () => {
    const day1 = new Date('2025-06-15T10:00:00').getTime();
    const day2 = new Date('2025-06-16T10:00:00').getTime();
    const records = [
      createMockRecord({ id: '1', timestamp: day1, ghi: 800 }),
      createMockRecord({ id: '2', timestamp: day2, ghi: 900 }),
    ];
    const groups = groupByDay(records);
    expect(Object.keys(groups).length).toBe(2);
  });

  it('should return empty object for empty records', () => {
    const groups = groupByDay([]);
    expect(Object.keys(groups).length).toBe(0);
  });
});

describe('Day Statistics', () => {
  it('should calculate min/max/avg correctly for a day', () => {
    const baseTime = new Date('2025-06-15T08:00:00').getTime();
    const records = [
      createMockRecord({ id: '1', timestamp: baseTime, ghi: 200, tempCell: 30, pExp: 70 }),
      createMockRecord({ id: '2', timestamp: baseTime + 3600000, ghi: 800, tempCell: 50, pExp: 280 }),
      createMockRecord({ id: '3', timestamp: baseTime + 7200000, ghi: 1000, tempCell: 60, pExp: 340 }),
    ];

    const ghiValues = records.map(r => r.ghi);
    const tempValues = records.map(r => r.tempCell);
    const pExpValues = records.map(r => r.pExp);

    expect(Math.min(...ghiValues)).toBe(200);
    expect(Math.max(...ghiValues)).toBe(1000);
    expect(ghiValues.reduce((a, b) => a + b, 0) / ghiValues.length).toBeCloseTo(666.67, 0);

    expect(Math.min(...tempValues)).toBe(30);
    expect(Math.max(...tempValues)).toBe(60);

    expect(Math.min(...pExpValues)).toBe(70);
    expect(Math.max(...pExpValues)).toBe(340);
  });
});
