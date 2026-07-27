import { useState, useCallback, useRef } from 'react';
import { toast } from 'sonner';
import { FileUp, Loader2, CheckCircle2, AlertTriangle, X, FileText, Zap, Thermometer, Ruler, Info } from 'lucide-react';
import { trpc } from '@/lib/trpc';
import type { PanelTechnology } from '@/lib/panelTechnologies';

interface ExtractedParams {
  name: string;
  manufacturer: string;
  model: string;
  pmax: number | null;
  voc: number | null;
  isc: number | null;
  vmp: number | null;
  imp: number | null;
  efficiencySTC: number | null;
  tempCoeffPmax: number | null;
  tempCoeffVoc: number | null;
  tempCoeffIsc: number | null;
  lengthMm: number | null;
  widthMm: number | null;
  weightKg: number | null;
  noct: number | null;
  degradationAnnual: number | null;
  cellType: string | null;
  application: string | null;
  confidence: 'high' | 'medium' | 'low';
  warnings: string[];
}

interface PDFPanelImporterProps {
  /** Callback cuando el usuario acepta los parámetros extraídos */
  onApplyParams: (panel: Partial<PanelTechnology>) => void;
  /** Texto del botón de colapso (opcional) */
  compact?: boolean;
}

const CONFIDENCE_STYLES = {
  high: { bg: 'bg-green-50 border-green-200', text: 'text-green-700', icon: CheckCircle2, label: 'Alta' },
  medium: { bg: 'bg-yellow-50 border-yellow-200', text: 'text-yellow-700', icon: AlertTriangle, label: 'Media' },
  low: { bg: 'bg-red-50 border-red-200', text: 'text-red-700', icon: AlertTriangle, label: 'Baja' },
};

const CELL_TYPE_TO_PVGIS: Record<string, string> = {
  'mono-Si': 'crystSi',
  'poly-Si': 'crystSi',
  'HJT': 'crystSi',
  'TOPCon': 'crystSi',
  'CdTe': 'CdTe',
  'CIGS': 'CIS',
  'CIS': 'CIS',
  'a-Si': 'Unknown',
  'perovskite': 'Unknown',
};

export default function PDFPanelImporter({ onApplyParams, compact = false }: PDFPanelImporterProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [isExtracting, setIsExtracting] = useState(false);
  const [extracted, setExtracted] = useState<ExtractedParams | null>(null);
  const [fileName, setFileName] = useState<string>('');
  const [isExpanded, setIsExpanded] = useState(!compact);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const extractMutation = trpc.customPanels.extractFromPDF.useMutation();

  const processFile = useCallback(async (file: File) => {
    if (file.type !== 'application/pdf') {
      toast.error('Solo se aceptan archivos PDF');
      return;
    }
    if (file.size > 16 * 1024 * 1024) {
      toast.error('El archivo excede el límite de 16MB');
      return;
    }

    setFileName(file.name);
    setIsExtracting(true);
    setExtracted(null);

    try {
      // Convertir a base64
      const arrayBuffer = await file.arrayBuffer();
      const base64 = btoa(
        new Uint8Array(arrayBuffer).reduce((data, byte) => data + String.fromCharCode(byte), '')
      );

      const result = await extractMutation.mutateAsync({
        fileBase64: base64,
        fileName: file.name,
      });

      setExtracted(result);
      toast.success(`Parámetros extraídos de "${file.name}" (confianza: ${result.confidence})`);
    } catch (err: any) {
      toast.error(`Error al extraer parámetros: ${err.message || 'Error desconocido'}`);
    } finally {
      setIsExtracting(false);
    }
  }, [extractMutation]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) processFile(file);
  }, [processFile]);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) processFile(file);
    // Reset input para permitir re-selección del mismo archivo
    if (fileInputRef.current) fileInputRef.current.value = '';
  }, [processFile]);

  const handleApply = useCallback(() => {
    if (!extracted) return;

    const pvgisTechchoice = extracted.cellType
      ? CELL_TYPE_TO_PVGIS[extracted.cellType] || 'Unknown'
      : 'crystSi';

    const panel: Partial<PanelTechnology> = {
      name: extracted.name || `${extracted.manufacturer} ${extracted.model}`,
      description: `Importado desde PDF: ${fileName}. Tipo: ${extracted.cellType || 'N/A'}`,
      pmax: extracted.pmax ?? 400,
      voc: extracted.voc ?? 40,
      isc: extracted.isc ?? 10,
      vmp: extracted.vmp ?? 33,
      imp: extracted.imp ?? 9.5,
      efficiencySTC: extracted.efficiencySTC ?? 20,
      tempCoeffPmax: extracted.tempCoeffPmax ?? -0.35,
      lengthMm: extracted.lengthMm ?? 1700,
      widthMm: extracted.widthMm ?? 1000,
      weightKg: extracted.weightKg ?? 22,
      noct: extracted.noct ?? 45,
      degradationAnnual: extracted.degradationAnnual ?? 0.55,
      systemLoss: 14,
      pvgisTechchoice,
      pvgisMountingplace: 'building' as const,
      application: extracted.application || 'Panel importado desde ficha técnica',
      isCustom: true,
      color: '#8B5CF6',
    };

    onApplyParams(panel);
    toast.success('Parámetros aplicados al formulario de panel personalizado');
  }, [extracted, fileName, onApplyParams]);

  const handleReset = useCallback(() => {
    setExtracted(null);
    setFileName('');
  }, []);

  if (compact && !isExpanded) {
    return (
      <button
        onClick={() => setIsExpanded(true)}
        className="flex items-center gap-2 text-xs px-3 py-2 bg-violet-50 hover:bg-violet-100 border border-violet-200 rounded-lg text-violet-700 font-medium transition-colors"
      >
        <FileUp size={14} />
        Importar desde PDF
      </button>
    );
  }

  return (
    <div className="bg-gradient-to-br from-violet-50 to-indigo-50 border-2 border-violet-200 rounded-xl p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-bold text-violet-900 flex items-center gap-2">
          <FileText size={16} className="text-violet-600" />
          Importar Ficha Técnica PDF
        </h4>
        {compact && (
          <button onClick={() => { setIsExpanded(false); handleReset(); }} className="text-gray-400 hover:text-gray-600">
            <X size={16} />
          </button>
        )}
      </div>

      <p className="text-xs text-gray-600">
        Suba la ficha técnica (datasheet) del panel solar en formato PDF. El sistema extraerá automáticamente los parámetros eléctricos, térmicos y dimensionales usando IA.
      </p>

      {/* Zona de Drop */}
      {!extracted && !isExtracting && (
        <div
          onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
          onDragLeave={() => setIsDragOver(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all ${
            isDragOver
              ? 'border-violet-500 bg-violet-100/50 scale-[1.01]'
              : 'border-gray-300 bg-white/50 hover:border-violet-400 hover:bg-violet-50/50'
          }`}
        >
          <FileUp size={32} className={`mx-auto mb-2 ${isDragOver ? 'text-violet-600' : 'text-gray-400'}`} />
          <p className="text-sm font-medium text-gray-700">
            {isDragOver ? 'Suelte el archivo aquí' : 'Arrastre un PDF o haga clic para seleccionar'}
          </p>
          <p className="text-xs text-gray-500 mt-1">Máximo 16MB · Solo archivos .pdf</p>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,application/pdf"
            onChange={handleFileSelect}
            className="hidden"
          />
        </div>
      )}

      {/* Estado de extracción */}
      {isExtracting && (
        <div className="bg-white border border-violet-200 rounded-xl p-6 text-center">
          <Loader2 size={32} className="mx-auto mb-3 text-violet-600 animate-spin" />
          <p className="text-sm font-semibold text-violet-800">Analizando ficha técnica...</p>
          <p className="text-xs text-gray-500 mt-1">"{fileName}" · Extrayendo parámetros con IA</p>
          <p className="text-xs text-gray-400 mt-2">Esto puede tardar 10-20 segundos</p>
        </div>
      )}

      {/* Resultados de extracción */}
      {extracted && (
        <div className="space-y-3">
          {/* Header con confianza */}
          <div className={`flex items-center justify-between p-3 rounded-lg border ${CONFIDENCE_STYLES[extracted.confidence].bg}`}>
            <div className="flex items-center gap-2">
              {(() => {
                const Icon = CONFIDENCE_STYLES[extracted.confidence].icon;
                return <Icon size={16} className={CONFIDENCE_STYLES[extracted.confidence].text} />;
              })()}
              <span className={`text-sm font-semibold ${CONFIDENCE_STYLES[extracted.confidence].text}`}>
                Confianza: {CONFIDENCE_STYLES[extracted.confidence].label}
              </span>
              <span className="text-xs text-gray-500">· {fileName}</span>
            </div>
            <button onClick={handleReset} className="text-xs text-gray-500 hover:text-red-600 font-medium">
              ✕ Descartar
            </button>
          </div>

          {/* Warnings */}
          {extracted.warnings.length > 0 && (
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
              <p className="text-xs font-semibold text-amber-800 mb-1 flex items-center gap-1">
                <Info size={12} /> Advertencias:
              </p>
              <ul className="text-xs text-amber-700 space-y-0.5">
                {extracted.warnings.map((w, i) => (
                  <li key={i}>• {w}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Datos extraídos */}
          <div className="bg-white border border-gray-200 rounded-xl p-4 space-y-3">
            {/* Identificación */}
            <div>
              <p className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-1">Identificación</p>
              <p className="text-sm font-semibold text-gray-900">{extracted.name}</p>
              <p className="text-xs text-gray-600">{extracted.manufacturer} · {extracted.model} · {extracted.cellType || 'N/A'}</p>
            </div>

            {/* Parámetros eléctricos */}
            <div>
              <p className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-2 flex items-center gap-1">
                <Zap size={12} /> Eléctricos STC
              </p>
              <div className="grid grid-cols-3 md:grid-cols-6 gap-2">
                <ParamBox label="Pmax" value={extracted.pmax} unit="W" />
                <ParamBox label="Voc" value={extracted.voc} unit="V" />
                <ParamBox label="Isc" value={extracted.isc} unit="A" />
                <ParamBox label="Vmp" value={extracted.vmp} unit="V" />
                <ParamBox label="Imp" value={extracted.imp} unit="A" />
                <ParamBox label="η" value={extracted.efficiencySTC} unit="%" />
              </div>
            </div>

            {/* Térmicos */}
            <div>
              <p className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-2 flex items-center gap-1">
                <Thermometer size={12} /> Térmicos
              </p>
              <div className="grid grid-cols-3 md:grid-cols-4 gap-2">
                <ParamBox label="γ Pmax" value={extracted.tempCoeffPmax} unit="%/°C" />
                <ParamBox label="γ Voc" value={extracted.tempCoeffVoc} unit="%/°C" />
                <ParamBox label="γ Isc" value={extracted.tempCoeffIsc} unit="%/°C" />
                <ParamBox label="NOCT" value={extracted.noct} unit="°C" />
              </div>
            </div>

            {/* Dimensiones */}
            <div>
              <p className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-2 flex items-center gap-1">
                <Ruler size={12} /> Dimensiones
              </p>
              <div className="grid grid-cols-3 md:grid-cols-4 gap-2">
                <ParamBox label="Largo" value={extracted.lengthMm} unit="mm" />
                <ParamBox label="Ancho" value={extracted.widthMm} unit="mm" />
                <ParamBox label="Peso" value={extracted.weightKg} unit="kg" />
                <ParamBox label="Degradación" value={extracted.degradationAnnual} unit="%/año" />
              </div>
            </div>
          </div>

          {/* Botones de acción */}
          <div className="flex gap-2">
            <button
              onClick={handleApply}
              className="flex-1 flex items-center justify-center gap-2 py-2.5 bg-violet-600 hover:bg-violet-500 text-white rounded-lg font-semibold text-sm transition-colors shadow-sm"
            >
              <CheckCircle2 size={16} />
              Aplicar Parámetros al Panel Personalizado
            </button>
            <button
              onClick={() => fileInputRef.current?.click()}
              className="px-4 py-2.5 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg font-medium text-sm transition-colors border border-gray-200"
            >
              Otro PDF
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,application/pdf"
              onChange={handleFileSelect}
              className="hidden"
            />
          </div>
        </div>
      )}
    </div>
  );
}

function ParamBox({ label, value, unit }: { label: string; value: number | null; unit: string }) {
  return (
    <div className={`rounded-lg p-2 text-center border ${value !== null ? 'bg-gray-50 border-gray-200' : 'bg-red-50 border-red-200'}`}>
      <p className="text-[10px] text-gray-500 font-medium">{label}</p>
      <p className={`text-sm font-bold ${value !== null ? 'text-gray-800' : 'text-red-400'}`}>
        {value !== null ? (typeof value === 'number' && !Number.isInteger(value) ? value.toFixed(2) : value) : '—'}
      </p>
      <p className="text-[9px] text-gray-400">{unit}</p>
    </div>
  );
}
