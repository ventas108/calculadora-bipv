import { useState, useEffect } from 'react';
import { FileText, Download, Loader, AlertTriangle, Save, Trash2, BarChart3 } from 'lucide-react';
import { toast } from 'sonner';
import { generateSolarReport, MultiFacadeData } from '@/lib/reportGenerator';
import { generateGlobalReport } from '@/lib/globalReportGenerator';
import { EPWData } from '@/lib/epwParser';
import { FacadeFullAnalysis } from '@/lib/facadeShadingAnalysis';

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

export interface StoredFacadeReport {
  id: string;
  facadeName: string;
  timestamp: number;
  data: {
    city: string;
    country: string;
    latitude: number;
    longitude: number;
    elevation: number;
    tilt: number;
    azimuth: number;
    area: number;
    panelPower: number;
    panelEfficiency: number;
    panelQuantity: number;
    annualProduction: number;
    capacityFactor: number;
    performanceRatio: number;
    systemLosses: number;
    paybackPeriod: number;
    roi10Year: number;
    roi25Year: number;
    annualFS: number;
    annualShadingLoss: number;
    annualPOA: number;
    annualPOANoShading: number;
    fsJunSolstice: number;
    fsDecSolstice: number;
  };
}

interface ReportGeneratorProps {
  city: string;
  country: string;
  latitude: number;
  longitude: number;
  elevation: number;
  shadingPoints: ShadingPoint[];
  poaData: POAData[];
  weatherData: EPWData | null;
  panelPower: number;
  panelEfficiency: number;
  panelArea: number;
  panelQuantity: number;
  tilt: number;
  azimuth: number;
  annualProduction: number;
  capacityFactor: number;
  performanceRatio: number;
  systemLosses: number;
  paybackPeriod: number;
  roi10Year: number;
  roi25Year: number;
  multiFacadeData?: MultiFacadeData;
  facadeAnalysis3D?: FacadeFullAnalysis | null;
}

const STORAGE_KEY = 'solar_facade_reports';

function loadStoredReports(): StoredFacadeReport[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function saveStoredReports(reports: StoredFacadeReport[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(reports));
}

export default function ReportGenerator({
  city,
  country,
  latitude,
  longitude,
  elevation,
  shadingPoints,
  poaData,
  weatherData,
  panelPower,
  panelEfficiency,
  panelArea,
  panelQuantity,
  tilt,
  azimuth,
  annualProduction,
  capacityFactor,
  performanceRatio,
  systemLosses,
  paybackPeriod,
  roi10Year,
  roi25Year,
  multiFacadeData,
  facadeAnalysis3D,
}: ReportGeneratorProps) {
  const [generating, setGenerating] = useState(false);
  const [generatingGlobal, setGeneratingGlobal] = useState(false);
  const [reportName, setReportName] = useState(`Reporte_Solar_${city.replace(/\s+/g, '_')}_${new Date().getFullYear()}`);
  const [storedReports, setStoredReports] = useState<StoredFacadeReport[]>(loadStoredReports());

  useEffect(() => {
    setStoredReports(loadStoredReports());
  }, []);

  const hasWeatherData = !!weatherData;
  const hasShadingPoints = shadingPoints.length > 0;
  const hasPoaData = poaData.length > 0;
  const canGenerate = hasWeatherData;
  const isFacadeSpecific = !!facadeAnalysis3D;

  const handleGenerateReport = async () => {
    if (!weatherData) {
      toast.error('Por favor carga datos meteorológicos (EPW) primero');
      return;
    }

    setGenerating(true);

    try {
      const reportData = {
        city,
        country,
        latitude,
        longitude,
        elevation,
        date: new Date().toLocaleDateString('es-ES'),
        shadingPoints,
        poaData,
        energyData: {
          panelPower,
          panelEfficiency,
          panelArea,
          quantity: panelQuantity,
          tilt,
          azimuth,
          annualProduction,
          capacityFactor,
          performanceRatio,
          systemLosses,
          paybackPeriod,
          roi10Year,
          roi25Year,
        },
        weatherData,
        multiFacadeData,
        facadeAnalysis3D,
      };

      const pdf = generateSolarReport(reportData);
      pdf.save(`${reportName}.pdf`);

      toast.success(`✓ Reporte generado: ${reportName}.pdf`);
    } catch (error) {
      console.error('Report generation error:', error);
      toast.error(`Error al generar el reporte: ${error instanceof Error ? error.message : 'Error desconocido'}`);
    } finally {
      setGenerating(false);
    }
  };

  const handleSaveToStorage = () => {
    if (!facadeAnalysis3D) {
      toast.error('Selecciona una fachada del modelo 3D en el Simulador antes de almacenar');
      return;
    }

    const fa = facadeAnalysis3D;
    const junData = fa.monthlyData.find(m => m.month === 6);
    const dicData = fa.monthlyData.find(m => m.month === 12);

    const report: StoredFacadeReport = {
      id: `${fa.facadeName}_${Date.now()}`,
      facadeName: fa.facadeName,
      timestamp: Date.now(),
      data: {
        city,
        country,
        latitude,
        longitude,
        elevation,
        tilt: fa.tilt,
        azimuth: fa.azimuth,
        area: fa.area,
        panelPower,
        panelEfficiency,
        panelQuantity,
        annualProduction,
        capacityFactor,
        performanceRatio,
        systemLosses,
        paybackPeriod,
        roi10Year,
        roi25Year,
        annualFS: fa.annualFS,
        annualShadingLoss: fa.annualShadingLoss,
        annualPOA: fa.annualPOA,
        annualPOANoShading: fa.annualPOANoShading,
        fsJunSolstice: junData ? junData.fsAverage : 1.0,
        fsDecSolstice: dicData ? dicData.fsAverage : 1.0,
      },
    };

    // Check if already stored for this facade
    const existing = storedReports.findIndex(r => r.facadeName === fa.facadeName);
    let updated: StoredFacadeReport[];
    if (existing >= 0) {
      updated = [...storedReports];
      updated[existing] = report;
      toast.success(`✓ Reporte actualizado: ${fa.facadeName}`);
    } else {
      updated = [...storedReports, report];
      toast.success(`✓ Reporte almacenado: ${fa.facadeName}`);
    }

    setStoredReports(updated);
    saveStoredReports(updated);
  };

  const handleDeleteStored = (id: string) => {
    const updated = storedReports.filter(r => r.id !== id);
    setStoredReports(updated);
    saveStoredReports(updated);
    toast.info('Reporte eliminado');
  };

  const handleClearAll = () => {
    setStoredReports([]);
    saveStoredReports([]);
    toast.info('Todos los reportes almacenados eliminados');
  };

  const handleGenerateGlobalReport = async () => {
    if (storedReports.length < 2) {
      toast.error('Necesitas al menos 2 reportes almacenados para generar el comparativo global');
      return;
    }

    setGeneratingGlobal(true);
    try {
      const pdf = generateGlobalReport(storedReports, {
        city,
        country,
        latitude,
        longitude,
        elevation,
      });
      pdf.save(`Reporte_Global_Comparativo_${city.replace(/\s+/g, '_')}_${new Date().getFullYear()}.pdf`);
      toast.success('✓ Reporte global comparativo generado');
    } catch (error) {
      console.error('Global report error:', error);
      toast.error(`Error: ${error instanceof Error ? error.message : 'Error desconocido'}`);
    } finally {
      setGeneratingGlobal(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Reporte Individual */}
      <div className="bg-gradient-to-r from-purple-50 to-pink-50 border border-purple-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <FileText size={20} className="text-purple-600" />
          Reporte Individual por Superficie
        </h3>

        {isFacadeSpecific && (
          <div className="bg-purple-100 border border-purple-300 rounded-lg p-3 mb-4">
            <p className="text-sm font-medium text-purple-900">
              Superficie activa: <strong>{facadeAnalysis3D!.facadeName}</strong>
            </p>
            <p className="text-xs text-purple-700 mt-1">
              Azimut: {facadeAnalysis3D!.azimuth.toFixed(0)}° | Tilt: {facadeAnalysis3D!.tilt.toFixed(0)}° | Área: {facadeAnalysis3D!.area.toFixed(1)} m²
            </p>
          </div>
        )}

        {!isFacadeSpecific && (
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 mb-4">
            <p className="text-sm text-amber-800">
              <AlertTriangle size={14} className="inline mr-1" />
              No hay fachada seleccionada del modelo 3D. El reporte será genérico. Para un reporte específico, selecciona una fachada en el Simulador.
            </p>
          </div>
        )}

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Nombre del Reporte</label>
            <input
              type="text"
              value={reportName}
              onChange={(e) => setReportName(e.target.value)}
              placeholder="Ej: Reporte_Solar_Cubierta_Norte"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <h4 className="font-semibold text-gray-900 mb-3">Resumen del Análisis</h4>
              <div className="space-y-2 text-sm">
                <p><strong>Ubicación:</strong> {city}, {country}</p>
                <p><strong>Producción Anual:</strong> {annualProduction > 0 ? `${annualProduction.toFixed(0)} kWh` : 'No calculada'}</p>
                <p><strong>Factor de Capacidad:</strong> {capacityFactor > 0 ? `${capacityFactor.toFixed(1)}%` : 'N/A'}</p>
                <p><strong>Payback:</strong> {paybackPeriod > 0 ? `${paybackPeriod.toFixed(1)} años` : 'N/A'}</p>
                {isFacadeSpecific && (
                  <>
                    <p><strong>FS Anual:</strong> {(facadeAnalysis3D!.annualFS * 100).toFixed(1)}%</p>
                    <p><strong>Pérdida Sombra:</strong> {facadeAnalysis3D!.annualShadingLoss.toFixed(1)}%</p>
                  </>
                )}
              </div>
            </div>

            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <h4 className="font-semibold text-gray-900 mb-3">Datos Incluidos</h4>
              <ul className="space-y-1 text-sm text-gray-700">
                <li className={hasWeatherData ? '' : 'opacity-50'}>
                  {hasWeatherData ? '✓' : '○'} Datos meteorológicos
                </li>
                <li className={isFacadeSpecific || hasShadingPoints ? '' : 'opacity-50'}>
                  {isFacadeSpecific || hasShadingPoints ? '✓' : '○'} Análisis de sombreado {isFacadeSpecific ? '(solsticios)' : `(${shadingPoints.length} puntos)`}
                </li>
                <li className={hasPoaData ? '' : 'opacity-50'}>
                  {hasPoaData ? '✓' : '○'} Radiación POA ({poaData.length} meses)
                </li>
                <li className={annualProduction > 0 ? '' : 'opacity-50'}>
                  {annualProduction > 0 ? '✓' : '○'} Proyecciones energéticas
                </li>
                <li className={paybackPeriod > 0 ? '' : 'opacity-50'}>
                  {paybackPeriod > 0 ? '✓' : '○'} Análisis financiero
                </li>
              </ul>
            </div>
          </div>

          <div className="flex gap-3">
            {/* Botón Descargar PDF */}
            <button
              onClick={handleGenerateReport}
              disabled={generating || !canGenerate}
              className="flex-1 px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors flex items-center justify-center gap-2 disabled:bg-gray-400 disabled:cursor-not-allowed font-medium"
            >
              {generating ? (
                <>
                  <Loader size={18} className="animate-spin" />
                  Generando...
                </>
              ) : (
                <>
                  <Download size={18} />
                  Descargar Reporte PDF
                </>
              )}
            </button>

            {/* Botón Almacenar */}
            <button
              onClick={handleSaveToStorage}
              disabled={!isFacadeSpecific || !canGenerate}
              className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center justify-center gap-2 disabled:bg-gray-400 disabled:cursor-not-allowed font-medium"
              title={!isFacadeSpecific ? 'Selecciona una fachada del modelo 3D primero' : 'Almacenar para reporte global'}
            >
              <Save size={18} />
              Almacenar
            </button>
          </div>
        </div>
      </div>

      {/* Reportes Almacenados */}
      <div className="bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <BarChart3 size={20} className="text-green-600" />
          Reportes Almacenados ({storedReports.length})
        </h3>

        {storedReports.length === 0 ? (
          <p className="text-sm text-gray-600 italic">
            No hay reportes almacenados. Selecciona una fachada en el Simulador, genera su análisis y haz clic en "Almacenar" para agregar superficies al comparativo global.
          </p>
        ) : (
          <>
            <div className="space-y-2 mb-4 max-h-60 overflow-y-auto">
              {storedReports.map((report) => (
                <div key={report.id} className="bg-white border border-gray-200 rounded-lg p-3 flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-900">{report.facadeName}</p>
                    <p className="text-xs text-gray-500">
                      {report.data.annualProduction.toFixed(0)} kWh/año | CF: {report.data.capacityFactor.toFixed(1)}% | FS: {(report.data.annualFS * 100).toFixed(1)}% | Payback: {report.data.paybackPeriod > 0 ? `${report.data.paybackPeriod.toFixed(1)} años` : 'N/A'}
                    </p>
                    <p className="text-xs text-gray-400">
                      {new Date(report.timestamp).toLocaleString('es-ES')}
                    </p>
                  </div>
                  <button
                    onClick={() => handleDeleteStored(report.id)}
                    className="p-2 text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                    title="Eliminar"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              ))}
            </div>

            <div className="flex gap-3">
              <button
                onClick={handleGenerateGlobalReport}
                disabled={generatingGlobal || storedReports.length < 2}
                className="flex-1 px-6 py-3 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors flex items-center justify-center gap-2 disabled:bg-gray-400 disabled:cursor-not-allowed font-medium"
              >
                {generatingGlobal ? (
                  <>
                    <Loader size={18} className="animate-spin" />
                    Generando...
                  </>
                ) : (
                  <>
                    <BarChart3 size={18} />
                    Generar Reporte Global Comparativo
                  </>
                )}
              </button>

              <button
                onClick={handleClearAll}
                className="px-4 py-3 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors flex items-center gap-2 font-medium text-sm"
              >
                <Trash2 size={16} />
                Limpiar
              </button>
            </div>

            {storedReports.length < 2 && (
              <p className="text-xs text-amber-600 mt-2">
                Necesitas al menos 2 superficies almacenadas para generar el reporte comparativo global.
              </p>
            )}
          </>
        )}
      </div>
    </div>
  );
}
