import { useState, useMemo } from 'react';
import { toast } from 'sonner';
import {
  Settings2, ChevronDown, ChevronUp, Save, RotateCcw, Info,
  Zap, Thermometer, Shield, PenLine, Ruler, Weight, Box,
  MapPin, CheckCircle2, AlertTriangle, XCircle,
} from 'lucide-react';
import PDFPanelImporter from './PDFPanelImporter';
import {
  PanelTechnology,
  PanelBrand,
  RegionalCompatibility,
  DEFAULT_PANEL_TECHNOLOGIES,
  createCustomTemplate,
  CATEGORY_LABELS,
  getTechnologiesByCategory,
} from '@/lib/panelTechnologies';
import type { RegionDetectionResult } from '@/lib/colombianRegions';

/** Regiones climáticas colombianas */
const COLOMBIAN_REGIONS: { key: keyof Omit<RegionalCompatibility, 'notes'>; label: string; cities: string }[] = [
  { key: 'caribe', label: 'Caribe', cities: 'Barranquilla, Cartagena, Santa Marta, Valledupar, Montería, Sincelejo, Riohacha' },
  { key: 'andina', label: 'Andina', cities: 'Bogotá, Medellín, Cali, Bucaramanga, Pereira, Manizales, Tunja, Ibagué' },
  { key: 'pacifica', label: 'Pacífica', cities: 'Quibdó, Buenaventura, Tumaco' },
  { key: 'orinoquia', label: 'Orinoquía', cities: 'Villavicencio, Yopal, Arauca' },
  { key: 'amazonia', label: 'Amazonía', cities: 'Leticia, Florencia, Mocoa, Puerto Asís' },
  { key: 'insular', label: 'Insular', cities: 'San Andrés, Providencia' },
];

const COMPAT_ICONS = {
  3: { icon: CheckCircle2, label: 'Óptimo', color: 'text-green-600', bg: 'bg-green-50 border-green-200' },
  2: { icon: AlertTriangle, label: 'Aceptable', color: 'text-yellow-600', bg: 'bg-yellow-50 border-yellow-200' },
  1: { icon: XCircle, label: 'No recomendado', color: 'text-red-500', bg: 'bg-red-50 border-red-200' },
};

const BRAND_LABELS: Record<PanelBrand, string> = {
  hiitio: 'HIITIO',
  einnova: 'EINNOVA',
  soltech: 'SOLTECH',
  generic: 'Genérico',
};

const BRAND_COLORS: Record<PanelBrand, { bg: string; text: string; border: string; activeBg: string }> = {
  hiitio: { bg: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-300', activeBg: 'bg-blue-600 text-white' },
  einnova: { bg: 'bg-emerald-50', text: 'text-emerald-700', border: 'border-emerald-300', activeBg: 'bg-emerald-600 text-white' },
  soltech: { bg: 'bg-purple-50', text: 'text-purple-700', border: 'border-purple-300', activeBg: 'bg-purple-600 text-white' },
  generic: { bg: 'bg-gray-50', text: 'text-gray-700', border: 'border-gray-300', activeBg: 'bg-gray-600 text-white' },
};

interface PanelTechSelectorProps {
  selectedTech: PanelTechnology;
  onSelectTech: (tech: PanelTechnology) => void;
  yearsFromInstall: number;
  onYearsChange: (years: number) => void;
  selectedRegion?: keyof Omit<RegionalCompatibility, 'notes'>;
  onRegionChange?: (region: keyof Omit<RegionalCompatibility, 'notes'>) => void;
  /** Información de auto-detección de región (para mostrar banner) */
  detectedRegionInfo?: RegionDetectionResult;
  /** Paneles personalizados persistentes (desde hook externo) */
  savedPanels?: PanelTechnology[];
  /** Callback para guardar un panel personalizado de forma persistente */
  onSavePanel?: (panel: PanelTechnology) => void;
  /** Callback para eliminar un panel personalizado persistente */
  onDeletePanel?: (panelId: string) => void;
}

export default function PanelTechSelector({
  selectedTech,
  onSelectTech,
  yearsFromInstall,
  onYearsChange,
  selectedRegion,
  onRegionChange,
  detectedRegionInfo,
  savedPanels,
  onSavePanel,
  onDeletePanel,
}: PanelTechSelectorProps) {
  const [showSelector, setShowSelector] = useState(false);
  const [showEditor, setShowEditor] = useState(false);
  const [editingTech, setEditingTech] = useState<PanelTechnology | null>(null);
  const [customTemplates, setCustomTemplates] = useState<PanelTechnology[]>([]);
  const [brandFilter, setBrandFilter] = useState<PanelBrand | 'all'>('all');
  const [internalRegion, setInternalRegion] = useState<keyof Omit<RegionalCompatibility, 'notes'>>('andina');

  const activeRegion = selectedRegion ?? internalRegion;
  const handleRegionChange = (r: keyof Omit<RegionalCompatibility, 'notes'>) => {
    if (onRegionChange) onRegionChange(r);
    else setInternalRegion(r);
  };

  const allTechnologies = useMemo(() => {
    return [...DEFAULT_PANEL_TECHNOLOGIES, ...customTemplates, ...(savedPanels ?? [])];
  }, [customTemplates, savedPanels]);

  const filteredTechnologies = useMemo(() => {
    if (brandFilter === 'all') return allTechnologies;
    return allTechnologies.filter(t => t.brand === brandFilter);
  }, [allTechnologies, brandFilter]);

  const categorized = useMemo(() => {
    return getTechnologiesByCategory(filteredTechnologies);
  }, [filteredTechnologies]);

  const handleSelectTech = (tech: PanelTechnology) => {
    onSelectTech(tech);
    setShowSelector(false);
    toast.success(`Seleccionado: ${tech.name}`);
  };

  const handleCreateCustom = (baseTech?: PanelTechnology) => {
    const custom = createCustomTemplate(baseTech);
    setEditingTech(custom);
    setShowEditor(true);
    setShowSelector(false);
  };

  const handleSaveCustom = () => {
    if (!editingTech) return;
    const existing = customTemplates.findIndex(t => t.id === editingTech.id);
    if (existing >= 0) {
      const updated = [...customTemplates];
      updated[existing] = editingTech;
      setCustomTemplates(updated);
    } else {
      setCustomTemplates([...customTemplates, editingTech]);
    }
    // Persistir externamente si hay callback
    if (onSavePanel) {
      onSavePanel(editingTech);
    }
    onSelectTech(editingTech);
    setShowEditor(false);
    setEditingTech(null);
    toast.success(`Plantilla "${editingTech.name}" guardada y seleccionada`);
  };

  const handleEditField = (field: keyof PanelTechnology, value: any) => {
    if (!editingTech) return;
    setEditingTech({ ...editingTech, [field]: value });
  };

  const handleEditCurrent = () => {
    const techToEdit = selectedTech.isCustom
      ? { ...selectedTech }
      : createCustomTemplate(selectedTech);
    setEditingTech(techToEdit);
    setShowEditor(true);
    setShowSelector(false);
  };

  // Área del módulo en m²
  const moduleArea = (selectedTech.lengthMm * selectedTech.widthMm) / 1e6;
  const wpPerM2 = selectedTech.pmax / moduleArea;

  // Compatibilidad regional del panel seleccionado
  const currentCompat = selectedTech.regionalCompatibility?.[activeRegion];
  const currentCompatInfo = currentCompat ? COMPAT_ICONS[currentCompat] : null;

  return (
    <div className="space-y-3" translate="no">
      {/* Tecnología seleccionada */}
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <div className="flex items-center justify-between mb-3">
          <h4 className="font-semibold text-gray-900 flex items-center gap-2">
            <Settings2 size={18} className="text-indigo-600" />
            <span>Tecnología del Panel</span>
          </h4>
          <div className="flex gap-2">
            <button
              onClick={handleEditCurrent}
              className="text-xs px-3 py-1.5 bg-indigo-50 text-indigo-700 rounded-md hover:bg-indigo-100 flex items-center gap-1 transition-colors"
            >
              <PenLine size={12} />
              <span>Editar</span>
            </button>
            <button
              onClick={() => { setShowSelector(!showSelector); setShowEditor(false); }}
              className="text-xs px-3 py-1.5 bg-blue-50 text-blue-700 rounded-md hover:bg-blue-100 flex items-center gap-1 transition-colors"
            >
              {showSelector ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
              <span>Cambiar</span>
            </button>
          </div>
        </div>

        {/* Info del panel seleccionado */}
        <div className="flex items-start gap-3 mb-3">
          <div
            className="w-10 h-10 rounded-lg flex items-center justify-center text-xs font-bold flex-shrink-0"
            style={{ backgroundColor: selectedTech.color + '20', border: `2px solid ${selectedTech.color}`, color: selectedTech.color }}
          >
            {selectedTech.hiitioId || 'GEN'}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <p className="font-medium text-gray-900 text-sm">{selectedTech.name}</p>
              {selectedTech.brand !== 'generic' && (
                <span className={`text-[9px] px-1.5 py-0.5 rounded-full font-semibold ${
                  selectedTech.brand === 'einnova' ? 'bg-emerald-100 text-emerald-700' :
                  selectedTech.brand === 'soltech' ? 'bg-purple-100 text-purple-700' :
                  'bg-blue-100 text-blue-700'
                }`}>
                  {BRAND_LABELS[selectedTech.brand]}
                </span>
              )}
            </div>
            <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">{selectedTech.description}</p>
          </div>
        </div>

        {/* Banner de auto-detección de región */}
        {detectedRegionInfo && detectedRegionInfo.isInColombia && (
          <div className={`border rounded-md p-2 mb-3 flex items-center gap-2 ${
            detectedRegionInfo.confidence === 'alta' ? 'bg-green-50 border-green-200' :
            detectedRegionInfo.confidence === 'media' ? 'bg-yellow-50 border-yellow-200' :
            'bg-orange-50 border-orange-200'
          }`}>
            <MapPin size={14} className={`${
              detectedRegionInfo.confidence === 'alta' ? 'text-green-600' :
              detectedRegionInfo.confidence === 'media' ? 'text-yellow-600' :
              'text-orange-600'
            }`} />
            <div className="flex-1">
              <p className="text-xs font-medium text-gray-700">
                Región detectada: <span className="font-bold">{detectedRegionInfo.label}</span>
                <span className={`ml-1.5 text-[10px] px-1.5 py-0.5 rounded-full font-semibold ${
                  detectedRegionInfo.confidence === 'alta' ? 'bg-green-100 text-green-700' :
                  detectedRegionInfo.confidence === 'media' ? 'bg-yellow-100 text-yellow-700' :
                  'bg-orange-100 text-orange-700'
                }`}>
                  {detectedRegionInfo.confidence === 'alta' ? 'Alta confianza' :
                   detectedRegionInfo.confidence === 'media' ? 'Confianza media' : 'Baja confianza'}
                </span>
              </p>
              <p className="text-[10px] text-gray-500 mt-0.5">
                Ciudades cercanas: {detectedRegionInfo.nearestCities}
                {selectedRegion && selectedRegion !== detectedRegionInfo.region && (
                  <span className="ml-1 text-indigo-600 font-medium">
                    (anulada manualmente a {COLOMBIAN_REGIONS.find(r => r.key === selectedRegion)?.label})
                  </span>
                )}
              </p>
            </div>
          </div>
        )}

        {/* Compatibilidad regional (HIITIO y EINNOVA) */}
        {selectedTech.regionalCompatibility && (
          <div className={`border rounded-md p-2.5 mb-3 ${currentCompatInfo?.bg || 'bg-gray-50 border-gray-200'}`}>
            <div className="flex items-center gap-2 mb-1.5">
              <MapPin size={14} className={currentCompatInfo?.color || 'text-gray-500'} />
              <span className="text-xs font-semibold text-gray-700">Compatibilidad Regional — {COLOMBIAN_REGIONS.find(r => r.key === activeRegion)?.label}</span>
              {currentCompatInfo && (
                <span className={`flex items-center gap-1 text-xs font-bold ${currentCompatInfo.color}`}>
                  <currentCompatInfo.icon size={14} />
                  {currentCompatInfo.label} ({currentCompat}/3)
                </span>
              )}
            </div>
            <div className="flex flex-wrap gap-1 mb-1.5">
              {COLOMBIAN_REGIONS.map(r => {
                const val = selectedTech.regionalCompatibility![r.key];
                const ci = COMPAT_ICONS[val];
                return (
                  <button
                    key={r.key}
                    onClick={() => handleRegionChange(r.key)}
                    className={`text-[10px] px-2 py-1 rounded-md border transition-all ${
                      activeRegion === r.key
                        ? 'ring-2 ring-indigo-400 border-indigo-400 bg-indigo-50 font-bold'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                    title={`${r.label}: ${ci.label} (${val}/3)\n${r.cities}`}
                  >
                    <span className={ci.color}>{r.label} </span>
                    <span className="font-bold">{val === 3 ? '★★★' : val === 2 ? '★★☆' : '★☆☆'}</span>
                  </button>
                );
              })}
            </div>
            {selectedTech.regionalCompatibility.notes && (
              <p className="text-[10px] text-gray-600 italic">{selectedTech.regionalCompatibility.notes}</p>
            )}
          </div>
        )}

        {/* Parámetros eléctricos STC */}
        <div className="grid grid-cols-3 sm:grid-cols-6 gap-2 mb-3">
          <div className="bg-yellow-50 rounded-md p-1.5 text-center">
            <p className="text-[9px] text-yellow-600 uppercase"><span>Pmax</span></p>
            <p className="text-xs font-bold text-yellow-800">{selectedTech.pmax}W</p>
          </div>
          <div className="bg-blue-50 rounded-md p-1.5 text-center">
            <p className="text-[9px] text-blue-600 uppercase"><span>Voc</span></p>
            <p className="text-xs font-bold text-blue-800">{selectedTech.voc}V</p>
          </div>
          <div className="bg-green-50 rounded-md p-1.5 text-center">
            <p className="text-[9px] text-green-600 uppercase"><span>Isc</span></p>
            <p className="text-xs font-bold text-green-800">{selectedTech.isc}A</p>
          </div>
          <div className="bg-indigo-50 rounded-md p-1.5 text-center">
            <p className="text-[9px] text-indigo-600 uppercase"><span>Efic. STC</span></p>
            <p className="text-xs font-bold text-indigo-800">{selectedTech.efficiencySTC}%</p>
          </div>
          <div className="bg-red-50 rounded-md p-1.5 text-center">
            <p className="text-[9px] text-red-600 uppercase"><span>Coef. T</span></p>
            <p className="text-xs font-bold text-red-800">{selectedTech.tempCoeffPmax}%/°C</p>
          </div>
          <div className="bg-orange-50 rounded-md p-1.5 text-center">
            <p className="text-[9px] text-orange-600 uppercase"><span>NOCT</span></p>
            <p className="text-xs font-bold text-orange-800">{selectedTech.noct}°C</p>
          </div>
        </div>

        {/* Datos físicos y PVGIS */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-3">
          <div className="bg-gray-50 rounded-md p-1.5">
            <p className="text-[9px] text-gray-500 flex items-center gap-0.5"><Ruler size={8} /><span>Dimensiones</span></p>
            <p className="text-xs font-medium text-gray-800">{selectedTech.lengthMm}x{selectedTech.widthMm}mm</p>
          </div>
          <div className="bg-gray-50 rounded-md p-1.5">
            <p className="text-[9px] text-gray-500 flex items-center gap-0.5"><Weight size={8} /><span>Peso</span></p>
            <p className="text-xs font-medium text-gray-800">{selectedTech.weightKg} kg</p>
          </div>
          <div className="bg-gray-50 rounded-md p-1.5">
            <p className="text-[9px] text-gray-500 flex items-center gap-0.5"><Zap size={8} /><span>Wp/m²</span></p>
            <p className="text-xs font-medium text-gray-800">{wpPerM2.toFixed(0)} Wp/m²</p>
          </div>
          <div className="bg-gray-50 rounded-md p-1.5">
            <p className="text-[9px] text-gray-500 flex items-center gap-0.5"><Box size={8} /><span>PVGIS Tech</span></p>
            <p className="text-xs font-medium text-gray-800">{selectedTech.pvgisTechchoice} / {selectedTech.pvgisMountingplace}</p>
          </div>
        </div>

        {/* Aplicación BIPV */}
        <div className="bg-blue-50 border border-blue-100 rounded-md p-2 mb-3">
          <p className="text-[10px] text-blue-600 font-medium"><span>Aplicación BIPV recomendada:</span></p>
          <p className="text-xs text-blue-800">{selectedTech.application}</p>
        </div>

        {/* Años desde instalación */}
        <div className="flex items-center gap-3">
          <label className="text-xs text-gray-600 flex items-center gap-1 whitespace-nowrap">
            <Shield size={12} className="text-gray-400" />
            <span>Años desde instalación:</span>
          </label>
          <input
            type="number"
            min="0"
            max="40"
            value={yearsFromInstall}
            onChange={(e) => onYearsChange(Math.max(0, parseInt(e.target.value) || 0))}
            className="w-16 px-2 py-1 border border-gray-300 rounded text-sm text-center font-mono"
          />
          <span className="text-xs text-gray-500">
            <span>Degradación: </span>
            <span className="font-medium text-red-600">
              {yearsFromInstall === 0 ? '0.0' :
                (100 - (100 - 2.0) *
                  Math.pow(1 - selectedTech.degradationAnnual / 100, Math.max(0, yearsFromInstall - 1))).toFixed(1)
              }%
            </span>
          </span>
        </div>
      </div>

      {/* Selector de tecnologías */}
      <div style={{ display: showSelector ? 'block' : 'none' }}>
        <div className="bg-white border border-gray-200 rounded-lg p-4 space-y-4 max-h-[600px] overflow-y-auto">
          {/* Header con filtros de marca */}
          <div className="sticky top-0 bg-white pb-2 z-10 space-y-3">
            <div className="flex items-center justify-between">
              <h5 className="font-semibold text-gray-900 text-sm"><span>Catálogo BIPV</span></h5>
              <button
                onClick={() => handleCreateCustom()}
                className="text-xs px-3 py-1.5 bg-purple-50 text-purple-700 rounded-md hover:bg-purple-100 flex items-center gap-1"
              >
                <PenLine size={12} />
                <span>Crear Personalizada</span>
              </button>
            </div>

            {/* Filtros de marca */}
            <div className="flex gap-1.5 flex-wrap">
              <button
                onClick={() => setBrandFilter('all')}
                className={`text-xs px-3 py-1.5 rounded-md border transition-all font-medium ${
                  brandFilter === 'all'
                    ? 'bg-indigo-600 text-white border-indigo-600'
                    : 'bg-gray-50 text-gray-600 border-gray-200 hover:border-gray-300'
                }`}
              >
                Todos ({allTechnologies.length})
              </button>
              {(['hiitio', 'einnova', 'soltech', 'generic'] as PanelBrand[]).map(brand => {
                const count = allTechnologies.filter(t => t.brand === brand).length;
                const bc = BRAND_COLORS[brand];
                return (
                  <button
                    key={brand}
                    onClick={() => setBrandFilter(brand)}
                    className={`text-xs px-3 py-1.5 rounded-md border transition-all font-medium ${
                      brandFilter === brand
                        ? bc.activeBg + ' border-transparent'
                        : `${bc.bg} ${bc.text} ${bc.border} hover:opacity-80`
                    }`}
                  >
                    {BRAND_LABELS[brand]} ({count})
                  </button>
                );
              })}
            </div>

            {/* Selector de región para filtrar compatibilidad */}
            {(brandFilter === 'einnova' || brandFilter === 'hiitio' || brandFilter === 'all') && (
              <div className="flex items-center gap-2 flex-wrap">
                <MapPin size={14} className="text-emerald-600" />
                <span className="text-xs font-medium text-gray-600">Región:</span>
                {COLOMBIAN_REGIONS.map(r => (
                  <button
                    key={r.key}
                    onClick={() => handleRegionChange(r.key)}
                    className={`text-[10px] px-2 py-1 rounded-md border transition-all ${
                      activeRegion === r.key
                        ? 'ring-2 ring-emerald-400 border-emerald-400 bg-emerald-50 font-bold text-emerald-700'
                        : 'border-gray-200 hover:border-gray-300 text-gray-600'
                    }`}
                    title={r.cities}
                  >
                    {r.label}
                  </button>
                ))}
              </div>
            )}
          </div>

          {Object.entries(categorized).map(([catKey, techs]) => {
            if (techs.length === 0) return null;
            return (
              <div key={catKey}>
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                  <span>{CATEGORY_LABELS[catKey]}</span>
                </p>
                <div className="grid grid-cols-1 gap-1.5">
                  {techs.map(tech => {
                    const compat = tech.regionalCompatibility?.[activeRegion];
                    const compatInfo = compat ? COMPAT_ICONS[compat] : null;
                    return (
                      <button
                        key={tech.id}
                        onClick={() => handleSelectTech(tech)}
                        className={`text-left p-2.5 rounded-lg border transition-all hover:shadow-sm ${
                          selectedTech.id === tech.id
                            ? 'border-blue-400 bg-blue-50 ring-1 ring-blue-200'
                            : 'border-gray-200 hover:border-gray-300 bg-white'
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          <div
                            className="w-8 h-8 rounded flex items-center justify-center text-[9px] font-bold flex-shrink-0"
                            style={{ backgroundColor: tech.color + '20', border: `1.5px solid ${tech.color}`, color: tech.color }}
                          >
                            {tech.hiitioId || 'GEN'}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-1.5">
                              <p className="text-xs font-medium text-gray-900 truncate">{tech.name}</p>
                              {compatInfo && (
                                <span className={`flex items-center gap-0.5 text-[9px] font-bold ${compatInfo.color} flex-shrink-0`}>
                                  <compatInfo.icon size={10} />
                                  {compat}/3
                                </span>
                              )}
                            </div>
                            <p className="text-[10px] text-gray-500">
                              <span>{tech.pmax}W · η={tech.efficiencySTC}% · γ={tech.tempCoeffPmax}%/°C · {tech.pvgisTechchoice}</span>
                            </p>
                          </div>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Editor de plantilla */}
      <div style={{ display: showEditor && editingTech ? 'block' : 'none' }}>
        {editingTech && (
          <div className="bg-white border-2 border-indigo-200 rounded-lg p-4 space-y-4">
            <div className="flex items-center justify-between">
              <h5 className="font-semibold text-gray-900 text-sm flex items-center gap-2">
                <PenLine size={16} className="text-indigo-600" />
                <span>Editor de Plantilla</span>
              </h5>
              <div className="flex gap-2">
                <button
                  onClick={() => { setShowEditor(false); setEditingTech(null); }}
                  className="text-xs px-3 py-1.5 bg-gray-100 text-gray-600 rounded-md hover:bg-gray-200 flex items-center gap-1"
                >
                  <RotateCcw size={12} />
                  <span>Cancelar</span>
                </button>
                <button
                  onClick={handleSaveCustom}
                  className="text-xs px-3 py-1.5 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 flex items-center gap-1"
                >
                  <Save size={12} />
                  <span>Guardar</span>
                </button>
              </div>
            </div>

            {/* Importar desde PDF */}
            <PDFPanelImporter
              compact
              onApplyParams={(partial) => {
                setEditingTech(prev => prev ? { ...prev, ...partial } : prev);
                toast.success('Campos del formulario actualizados desde el PDF');
              }}
            />

            {/* Nombre */}
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1"><span>Nombre</span></label>
              <input
                type="text"
                value={editingTech.name}
                onChange={(e) => handleEditField('name', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
              />
            </div>

            {/* Parámetros eléctricos */}
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 flex items-center gap-1">
                <Zap size={12} className="text-yellow-500" />
                <span>Parámetros Eléctricos STC</span>
              </p>
              <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
                {([
                  ['pmax', 'Pmax (W)', 0.1],
                  ['voc', 'Voc (V)', 0.01],
                  ['isc', 'Isc (A)', 0.01],
                  ['vmp', 'Vmp (V)', 0.01],
                  ['imp', 'Imp (A)', 0.01],
                  ['efficiencySTC', 'Efic. (%)', 0.1],
                ] as [keyof PanelTechnology, string, number][]).map(([field, label, step]) => (
                  <div key={field}>
                    <label className="block text-[10px] text-gray-500 mb-0.5"><span>{label}</span></label>
                    <input
                      type="number"
                      step={step}
                      value={editingTech[field] as number}
                      onChange={(e) => handleEditField(field, parseFloat(e.target.value) || 0)}
                      className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm font-mono"
                    />
                  </div>
                ))}
              </div>
            </div>

            {/* Parámetros térmicos */}
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 flex items-center gap-1">
                <Thermometer size={12} className="text-red-500" />
                <span>Térmicos y Sistema</span>
              </p>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                <div>
                  <label className="block text-[10px] text-gray-500 mb-0.5"><span>Coef. T Pmax (%/°C)</span></label>
                  <input
                    type="number"
                    step="0.01"
                    value={editingTech.tempCoeffPmax}
                    onChange={(e) => handleEditField('tempCoeffPmax', parseFloat(e.target.value) || 0)}
                    className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm font-mono"
                  />
                </div>
                <div>
                  <label className="block text-[10px] text-gray-500 mb-0.5"><span>NOCT (°C)</span></label>
                  <input
                    type="number"
                    step="1"
                    value={editingTech.noct}
                    onChange={(e) => handleEditField('noct', parseInt(e.target.value) || 43)}
                    className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm font-mono"
                  />
                </div>
                <div>
                  <label className="block text-[10px] text-gray-500 mb-0.5"><span>Pérdidas Sist. (%)</span></label>
                  <input
                    type="number"
                    step="0.5"
                    value={editingTech.systemLoss}
                    onChange={(e) => handleEditField('systemLoss', parseFloat(e.target.value) || 0)}
                    className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm font-mono"
                  />
                </div>
                <div>
                  <label className="block text-[10px] text-gray-500 mb-0.5"><span>Degradación (%/año)</span></label>
                  <input
                    type="number"
                    step="0.05"
                    value={editingTech.degradationAnnual}
                    onChange={(e) => handleEditField('degradationAnnual', parseFloat(e.target.value) || 0)}
                    className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm font-mono"
                  />
                </div>
              </div>
            </div>

            {/* Dimensiones */}
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 flex items-center gap-1">
                <Ruler size={12} className="text-blue-500" />
                <span>Dimensiones y PVGIS</span>
              </p>
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
                <div>
                  <label className="block text-[10px] text-gray-500 mb-0.5"><span>Largo (mm)</span></label>
                  <input
                    type="number"
                    value={editingTech.lengthMm}
                    onChange={(e) => handleEditField('lengthMm', parseInt(e.target.value) || 0)}
                    className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm font-mono"
                  />
                </div>
                <div>
                  <label className="block text-[10px] text-gray-500 mb-0.5"><span>Ancho (mm)</span></label>
                  <input
                    type="number"
                    value={editingTech.widthMm}
                    onChange={(e) => handleEditField('widthMm', parseInt(e.target.value) || 0)}
                    className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm font-mono"
                  />
                </div>
                <div>
                  <label className="block text-[10px] text-gray-500 mb-0.5"><span>Peso (kg)</span></label>
                  <input
                    type="number"
                    step="0.1"
                    value={editingTech.weightKg}
                    onChange={(e) => handleEditField('weightKg', parseFloat(e.target.value) || 0)}
                    className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm font-mono"
                  />
                </div>
                <div>
                  <label className="block text-[10px] text-gray-500 mb-0.5"><span>PVGIS Tech</span></label>
                  <select
                    value={editingTech.pvgisTechchoice}
                    onChange={(e) => handleEditField('pvgisTechchoice', e.target.value)}
                    className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm"
                  >
                    <option value="crystSi">crystSi</option>
                    <option value="CdTe">CdTe</option>
                    <option value="CIS">CIS/CIGS</option>
                    <option value="Unknown">Otro</option>
                  </select>
                </div>
                <div>
                  <label className="block text-[10px] text-gray-500 mb-0.5"><span>Montaje</span></label>
                  <select
                    value={editingTech.pvgisMountingplace}
                    onChange={(e) => handleEditField('pvgisMountingplace', e.target.value)}
                    className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm"
                  >
                    <option value="free">Rack abierto</option>
                    <option value="building">BIPV integrado</option>
                  </select>
                </div>
              </div>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 flex items-start gap-2">
              <Info size={14} className="text-blue-600 mt-0.5 flex-shrink-0" />
              <p className="text-xs text-blue-700">
                <span>Los parámetros se usan para: 1) enviar pvtechchoice/mountingplace a PVGIS, 2) calcular correcciones de temperatura con coef. real y NOCT, 3) ajustar pérdidas del sistema.</span>
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
