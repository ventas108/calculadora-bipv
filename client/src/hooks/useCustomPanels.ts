/**
 * Hook useCustomPanels
 *
 * Almacenamiento dual de paneles personalizados BIPV:
 * - localStorage: acceso inmediato sin login, persistencia local
 * - Base de datos (via tRPC): sincronización cuando hay sesión activa
 *
 * Flujo:
 * 1. Al montar: carga desde localStorage inmediatamente
 * 2. Si hay sesión activa: carga desde DB y fusiona con localStorage
 * 3. Al guardar: escribe en localStorage + DB (si autenticado)
 * 4. Al eliminar: elimina de localStorage + DB (si autenticado)
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { trpc } from '@/lib/trpc';
import { useAuth } from '@/_core/hooks/useAuth';

const STORAGE_KEY = 'bipv_custom_panels';

export interface CustomPanelLocal {
  /** ID local (generado con Date.now) */
  localId: string;
  /** ID en base de datos (null si no sincronizado) */
  dbId: number | null;
  /** Nombre del panel */
  name: string;
  /** Potencia nominal STC (W) */
  powerRating: number;
  /** Eficiencia nominal (%) */
  efficiency: number;
  /** Coeficiente de temperatura (%/°C) */
  tempCoeff: number;
  /** NOCT (°C) */
  noct: number;
  /** Área del panel (m²) */
  area: number;
  /** Degradación anual (%/año) */
  degradationAnnual: number;
  /** Voltaje circuito abierto (V) */
  voc?: number;
  /** Corriente cortocircuito (A) */
  isc?: number;
  /** Voltaje punto máx. potencia (V) */
  vmp?: number;
  /** Corriente punto máx. potencia (A) */
  imp?: number;
  /** Largo (mm) */
  lengthMm?: number;
  /** Ancho (mm) */
  widthMm?: number;
  /** Peso (kg) */
  weightKg?: number;
  /** Pérdidas del sistema (%) */
  systemLoss?: number;
  /** Aplicación */
  application?: string;
  /** Timestamp de creación */
  createdAt: number;
  /** Sincronizado con DB */
  synced: boolean;
}

function loadFromLocalStorage(): CustomPanelLocal[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    return JSON.parse(raw) as CustomPanelLocal[];
  } catch {
    return [];
  }
}

function saveToLocalStorage(panels: CustomPanelLocal[]): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(panels));
  } catch {
    // localStorage full or unavailable
  }
}

export function useCustomPanels() {
  const [panels, setPanels] = useState<CustomPanelLocal[]>([]);
  const [isSyncing, setIsSyncing] = useState(false);
  const { user, isAuthenticated } = useAuth();
  const syncedRef = useRef(false);

  // tRPC queries/mutations
  const listQuery = trpc.customPanels.list.useQuery(undefined, {
    enabled: isAuthenticated,
    refetchOnWindowFocus: false,
  });
  const createMutation = trpc.customPanels.create.useMutation();
  const deleteMutation = trpc.customPanels.delete.useMutation();

  // Load from localStorage on mount
  useEffect(() => {
    const local = loadFromLocalStorage();
    setPanels(local);
  }, []);

  // Sync with DB when authenticated and data is available
  useEffect(() => {
    if (!isAuthenticated || !listQuery.data || syncedRef.current) return;
    syncedRef.current = true;
    setIsSyncing(true);

    const localPanels = loadFromLocalStorage();
    const dbPanels = listQuery.data;

    // Merge: DB panels take priority, local-only panels get pushed to DB
    const mergedMap = new Map<string, CustomPanelLocal>();

    // Add all DB panels
    dbPanels.forEach((dbPanel) => {
      const key = `db_${dbPanel.id}`;
      mergedMap.set(key, {
        localId: key,
        dbId: dbPanel.id,
        name: dbPanel.name,
        powerRating: dbPanel.powerRating,
        efficiency: dbPanel.efficiency,
        tempCoeff: dbPanel.tempCoeff,
        noct: dbPanel.noct,
        area: dbPanel.area,
        degradationAnnual: dbPanel.degradationAnnual,
        voc: dbPanel.voc ?? undefined,
        isc: dbPanel.isc ?? undefined,
        vmp: dbPanel.vmp ?? undefined,
        imp: dbPanel.imp ?? undefined,
        lengthMm: dbPanel.lengthMm ?? undefined,
        widthMm: dbPanel.widthMm ?? undefined,
        weightKg: dbPanel.weightKg ?? undefined,
        systemLoss: dbPanel.systemLoss ?? undefined,
        application: dbPanel.application ?? undefined,
        createdAt: new Date(dbPanel.createdAt).getTime(),
        synced: true,
      });
    });

    // Push local-only panels to DB
    const unsyncedLocal = localPanels.filter(p => !p.synced && !p.dbId);
    const syncPromises = unsyncedLocal.map(async (panel) => {
      try {
        const created = await createMutation.mutateAsync({
          name: panel.name,
          powerRating: panel.powerRating,
          efficiency: panel.efficiency,
          tempCoeff: panel.tempCoeff,
          noct: panel.noct,
          area: panel.area,
          degradationAnnual: panel.degradationAnnual,
          voc: panel.voc,
          isc: panel.isc,
          vmp: panel.vmp,
          imp: panel.imp,
          lengthMm: panel.lengthMm,
          widthMm: panel.widthMm,
          weightKg: panel.weightKg,
          systemLoss: panel.systemLoss,
          application: panel.application,
        });
        if (created) {
          const key = `db_${created.id}`;
          mergedMap.set(key, { ...panel, localId: key, dbId: created.id, synced: true });
        }
      } catch {
        // Keep as local-only
        mergedMap.set(panel.localId, panel);
      }
    });

    Promise.all(syncPromises).then(() => {
      const merged = Array.from(mergedMap.values()).sort((a, b) => b.createdAt - a.createdAt);
      setPanels(merged);
      saveToLocalStorage(merged);
      setIsSyncing(false);
    });
  }, [isAuthenticated, listQuery.data]);

  // Save panel
  const savePanel = useCallback(async (panelData: Omit<CustomPanelLocal, 'localId' | 'dbId' | 'createdAt' | 'synced'>) => {
    const newPanel: CustomPanelLocal = {
      ...panelData,
      localId: `local_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
      dbId: null,
      createdAt: Date.now(),
      synced: false,
    };

    // Try to save to DB if authenticated
    if (isAuthenticated) {
      try {
        const created = await createMutation.mutateAsync({
          name: panelData.name,
          powerRating: panelData.powerRating,
          efficiency: panelData.efficiency,
          tempCoeff: panelData.tempCoeff,
          noct: panelData.noct,
          area: panelData.area,
          degradationAnnual: panelData.degradationAnnual,
          voc: panelData.voc,
          isc: panelData.isc,
          vmp: panelData.vmp,
          imp: panelData.imp,
          lengthMm: panelData.lengthMm,
          widthMm: panelData.widthMm,
          weightKg: panelData.weightKg,
          systemLoss: panelData.systemLoss,
          application: panelData.application,
        });
        if (created) {
          newPanel.dbId = created.id;
          newPanel.localId = `db_${created.id}`;
          newPanel.synced = true;
        }
      } catch {
        // Save locally only
      }
    }

    setPanels(prev => {
      const updated = [newPanel, ...prev];
      saveToLocalStorage(updated);
      return updated;
    });

    return newPanel;
  }, [isAuthenticated, createMutation]);

  // Delete panel
  const deletePanel = useCallback(async (localId: string) => {
    const panel = panels.find(p => p.localId === localId);
    if (!panel) return;

    // Delete from DB if synced
    if (panel.dbId && isAuthenticated) {
      try {
        await deleteMutation.mutateAsync({ id: panel.dbId });
      } catch {
        // Continue with local delete
      }
    }

    setPanels(prev => {
      const updated = prev.filter(p => p.localId !== localId);
      saveToLocalStorage(updated);
      return updated;
    });
  }, [panels, isAuthenticated, deleteMutation]);

  // Get panel count
  const panelCount = panels.length;

  return {
    panels,
    panelCount,
    savePanel,
    deletePanel,
    isSyncing,
    isAuthenticated,
  };
}
