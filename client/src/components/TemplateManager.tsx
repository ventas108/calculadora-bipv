import { Button } from '@/components/ui/button';
import { Download } from 'lucide-react';

interface Template {
  name: string;
  description: string;
  data: string[][];
}

const TEMPLATES: Template[] = [
  {
    name: 'Analisis Invierno',
    description: 'Analisis de sombreado para los meses de invierno (Dic-Feb)',
    data: [
      ['Mes', 'Dia', 'Hora', 'Altura Solar', 'Acimut Solar', 'Obstaculo', 'Area Sombreada'],
      ['Dic', '21', '9', '20', '-60', 'Edificio Norte', '40'],
      ['Dic', '21', '12', '35', '0', 'Arbol', '25'],
      ['Dic', '21', '15', '25', '60', 'Chimenea', '15'],
      ['Ene', '21', '9', '22', '-60', 'Edificio Norte', '38'],
      ['Ene', '21', '12', '37', '0', 'Arbol', '20'],
      ['Ene', '21', '15', '27', '60', 'Chimenea', '10'],
      ['Feb', '21', '9', '28', '-50', 'Edificio Norte', '30'],
      ['Feb', '21', '12', '45', '0', 'Arbol', '15'],
      ['Feb', '21', '15', '35', '50', 'Chimenea', '5'],
    ],
  },
  {
    name: 'Analisis Verano',
    description: 'Analisis de sombreado para los meses de verano (Jun-Ago)',
    data: [
      ['Mes', 'Dia', 'Hora', 'Altura Solar', 'Acimut Solar', 'Obstaculo', 'Area Sombreada'],
      ['Jun', '21', '6', '25', '-90', 'Ninguno', '0'],
      ['Jun', '21', '12', '72', '0', 'Ninguno', '0'],
      ['Jun', '21', '18', '25', '90', 'Ninguno', '0'],
      ['Jul', '21', '6', '28', '-85', 'Ninguno', '0'],
      ['Jul', '21', '12', '75', '0', 'Ninguno', '0'],
      ['Jul', '21', '18', '28', '85', 'Ninguno', '0'],
      ['Ago', '21', '6', '32', '-80', 'Ninguno', '0'],
      ['Ago', '21', '12', '70', '0', 'Ninguno', '0'],
      ['Ago', '21', '18', '32', '80', 'Ninguno', '0'],
    ],
  },
  {
    name: 'Analisis Equinoccios',
    description: 'Analisis para equinoccios de primavera y otoño (Mar-May, Sep-Nov)',
    data: [
      ['Mes', 'Dia', 'Hora', 'Altura Solar', 'Acimut Solar', 'Obstaculo', 'Area Sombreada'],
      ['Mar', '21', '9', '35', '-60', 'Edificio Este', '20'],
      ['Mar', '21', '12', '52', '0', 'Ninguno', '0'],
      ['Mar', '21', '15', '35', '60', 'Edificio Oeste', '20'],
      ['Sep', '21', '9', '35', '-60', 'Edificio Este', '20'],
      ['Sep', '21', '12', '52', '0', 'Ninguno', '0'],
      ['Sep', '21', '15', '35', '60', 'Edificio Oeste', '20'],
      ['Oct', '21', '9', '28', '-65', 'Edificio Este', '30'],
      ['Oct', '21', '12', '45', '0', 'Arbol', '10'],
      ['Oct', '21', '15', '28', '65', 'Edificio Oeste', '30'],
    ],
  },
  {
    name: 'Analisis Completo Anual',
    description: 'Analisis completo para todo el año (un punto por mes)',
    data: [
      ['Mes', 'Dia', 'Hora', 'Altura Solar', 'Acimut Solar', 'Obstaculo', 'Area Sombreada'],
      ['Ene', '21', '12', '30', '0', 'Edificio', '25'],
      ['Feb', '21', '12', '40', '0', 'Edificio', '20'],
      ['Mar', '21', '12', '50', '0', 'Ninguno', '0'],
      ['Abr', '21', '12', '60', '0', 'Ninguno', '0'],
      ['May', '21', '12', '68', '0', 'Ninguno', '0'],
      ['Jun', '21', '12', '72', '0', 'Ninguno', '0'],
      ['Jul', '21', '12', '75', '0', 'Ninguno', '0'],
      ['Ago', '21', '12', '70', '0', 'Ninguno', '0'],
      ['Sep', '21', '12', '52', '0', 'Ninguno', '0'],
      ['Oct', '21', '12', '40', '0', 'Edificio', '15'],
      ['Nov', '21', '12', '30', '0', 'Edificio', '25'],
      ['Dic', '21', '12', '25', '0', 'Edificio', '30'],
    ],
  },
  {
    name: 'Analisis Multiples Obstaculos',
    description: 'Analisis con multiples obstaculos en diferentes direcciones',
    data: [
      ['Mes', 'Dia', 'Hora', 'Altura Solar', 'Acimut Solar', 'Obstaculo', 'Area Sombreada'],
      ['Ene', '21', '8', '15', '-90', 'Edificio Este', '50'],
      ['Ene', '21', '10', '25', '-45', 'Arbol Este', '30'],
      ['Ene', '21', '12', '35', '0', 'Chimenea Central', '10'],
      ['Ene', '21', '14', '25', '45', 'Arbol Oeste', '25'],
      ['Ene', '21', '16', '15', '90', 'Edificio Oeste', '45'],
      ['Jul', '21', '8', '30', '-90', 'Edificio Este', '20'],
      ['Jul', '21', '10', '50', '-45', 'Arbol Este', '5'],
      ['Jul', '21', '12', '75', '0', 'Chimenea Central', '0'],
      ['Jul', '21', '14', '50', '45', 'Arbol Oeste', '5'],
      ['Jul', '21', '16', '30', '90', 'Edificio Oeste', '20'],
    ],
  },
];

export default function TemplateManager({ onLoadTemplate }: { onLoadTemplate: (data: string[][]) => void }) {
  const downloadTemplate = (template: Template) => {
    const csv = template.data.map(row => row.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `plantilla_${template.name.toLowerCase().replace(/\s+/g, '_')}.csv`;
    a.click();
  };

  return (
    <div className="w-full space-y-6">
      <div className="space-y-2">
        <h2 className="text-2xl font-bold text-gray-900">Plantillas Predefinidas</h2>
        <p className="text-gray-600">Descarga una plantilla de ejemplo y completala con tus datos, luego importala en la calculadora.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {TEMPLATES.map((template, idx) => (
          <div key={idx} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
            <h3 className="font-semibold text-gray-900 mb-2">{template.name}</h3>
            <p className="text-sm text-gray-600 mb-4">{template.description}</p>
            <div className="text-xs text-gray-500 mb-4">
              <p><strong>Puntos de datos:</strong> {template.data.length - 1}</p>
            </div>
            <div className="flex gap-2">
              <Button
                onClick={() => downloadTemplate(template)}
                variant="outline"
                className="flex-1 flex items-center justify-center gap-2"
              >
                <Download size={16} />
                Descargar CSV
              </Button>
              <Button
                onClick={() => onLoadTemplate(template.data)}
                className="flex-1 bg-blue-600 hover:bg-blue-700 text-white"
              >
                Cargar
              </Button>
            </div>
          </div>
        ))}
      </div>

      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
        <h3 className="font-semibold text-amber-900 mb-2">Instrucciones:</h3>
        <ol className="text-sm text-amber-800 space-y-1 list-decimal list-inside">
          <li>Selecciona una plantilla que se adapte a tu caso</li>
          <li>Haz clic en "Descargar CSV" para obtener el archivo</li>
          <li>Abre el archivo en Excel o un editor de texto</li>
          <li>Modifica los valores segun tu analisis</li>
          <li>Guarda el archivo y vuelve a la calculadora</li>
          <li>Haz clic en "Importar CSV" y selecciona tu archivo</li>
          <li>Los datos se cargaran automaticamente en la tabla</li>
        </ol>
      </div>
    </div>
  );
}
