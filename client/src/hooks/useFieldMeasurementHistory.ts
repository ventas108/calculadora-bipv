import { useState, useEffect, useCallback } from 'react';

export interface FieldMeasurementRecord {
  id: string;
  timestamp: number; // Unix ms
  label: string; // Etiqueta descriptiva (ej: "mañana nublado")
  // Valores de entrada
  ghi: number; // W/m²
  tempAmbient: number; // °C
  tempCell: number; // °C (calculada o manual)
  tempCellManual: boolean; // true si fue ingresada manualmente
  // Valores calculados
  pExp: number; // W (potencia esperada por módulo)
  pExpTotal: number; // kW (potencia total del sistema)
  prMulcue: number; // PR corregido (0-1)
  tempLoss: number; // Factor de pérdida por temperatura (0-1)
  // Contexto del panel
  panelName: string;
  panelPower: number; // W nominal
  panelQuantity: number;
  noct: number; // °C
  tempCoeff: number; // %/°C
  // Coordenadas de referencia
  latitude: number;
  longitude: number;
  cityName: string;
}

const STORAGE_KEY = 'solar_field_measurements_history';

export function useFieldMeasurementHistory() {
  const [records, setRecords] = useState<FieldMeasurementRecord[]>([]);

  // Cargar desde localStorage al montar
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored) as FieldMeasurementRecord[];
        // Ordenar por timestamp descendente (más reciente primero)
        setRecords(parsed.sort((a, b) => b.timestamp - a.timestamp));
      }
    } catch {
      // Si hay error de parsing, empezar con array vacío
      setRecords([]);
    }
  }, []);

  // Guardar en localStorage cada vez que cambian los records
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(records));
    } catch {
      // localStorage lleno o no disponible
    }
  }, [records]);

  const addRecord = useCallback((record: Omit<FieldMeasurementRecord, 'id' | 'timestamp'>) => {
    const newRecord: FieldMeasurementRecord = {
      ...record,
      id: `fm_${Date.now()}_${Math.random().toString(36).substring(2, 8)}`,
      timestamp: Date.now(),
    };
    setRecords(prev => [newRecord, ...prev]);
    return newRecord;
  }, []);

  const removeRecord = useCallback((id: string) => {
    setRecords(prev => prev.filter(r => r.id !== id));
  }, []);

  const clearAll = useCallback(() => {
    setRecords([]);
    localStorage.removeItem(STORAGE_KEY);
  }, []);

  const exportCSV = useCallback(() => {
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
  }, [records]);

  // Agrupar mediciones por día para facilitar la visualización
  const groupedByDay = useCallback(() => {
    const groups: Record<string, FieldMeasurementRecord[]> = {};
    records.forEach(r => {
      const dateKey = new Date(r.timestamp).toLocaleDateString('es-CO');
      if (!groups[dateKey]) groups[dateKey] = [];
      groups[dateKey].push(r);
    });
    // Ordenar cada grupo por hora ascendente
    Object.values(groups).forEach(group => group.sort((a, b) => a.timestamp - b.timestamp));
    return groups;
  }, [records]);

  return {
    records,
    addRecord,
    removeRecord,
    clearAll,
    exportCSV,
    groupedByDay,
    count: records.length,
  };
}
