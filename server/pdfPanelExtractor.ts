/**
 * PDF Panel Datasheet Extractor
 * 
 * Sube un PDF de ficha técnica de panel solar, extrae el texto,
 * y usa LLM con JSON schema para extraer los parámetros eléctricos/térmicos.
 */

import { invokeLLM } from "./_core/llm";
import { storagePut, storageGetSignedUrl } from "./storage";

// Interfaz de parámetros extraídos del PDF
export interface ExtractedPanelParams {
  name: string;
  manufacturer: string;
  model: string;
  // Eléctricos STC
  pmax: number | null;
  voc: number | null;
  isc: number | null;
  vmp: number | null;
  imp: number | null;
  efficiencySTC: number | null;  // en %
  tempCoeffPmax: number | null;  // en %/°C (negativo)
  tempCoeffVoc: number | null;   // en %/°C
  tempCoeffIsc: number | null;   // en %/°C
  // Dimensiones
  lengthMm: number | null;
  widthMm: number | null;
  weightKg: number | null;
  // Térmicos
  noct: number | null;
  // Sistema
  degradationAnnual: number | null;
  // Tipo de tecnología
  cellType: string | null;  // mono-Si, poly-Si, CdTe, CIGS, a-Si, perovskite, HJT, TOPCon
  // Aplicación
  application: string | null;
  // Confianza de la extracción
  confidence: 'high' | 'medium' | 'low';
  warnings: string[];
}

const EXTRACTION_SYSTEM_PROMPT = `Eres un experto en ingeniería fotovoltaica. Tu tarea es extraer los parámetros técnicos de una ficha técnica (datasheet) de un panel solar fotovoltaico.

INSTRUCCIONES:
1. Extrae TODOS los parámetros eléctricos en condiciones STC (Standard Test Conditions: 1000 W/m², 25°C, AM1.5).
2. Los coeficientes de temperatura deben estar en %/°C (negativos para Pmax y Voc, positivo para Isc).
3. Las dimensiones deben estar en milímetros (mm) y el peso en kilogramos (kg).
4. Si un valor no está disponible en el documento, usa null.
5. Para NOCT, busca "Nominal Operating Cell Temperature" o "NOCT" o "NMOT".
6. Para degradación anual, busca "annual degradation", "degradación" o infiere del warranty (típico 0.5-0.7%/año para Si cristalino).
7. Identifica el tipo de célula: mono-Si, poly-Si, CdTe, CIGS, a-Si, perovskite, HJT, TOPCon, bifacial.
8. La eficiencia debe estar en porcentaje (ej: 20.5 para 20.5%).
9. El coeficiente de temperatura de Pmax suele ser negativo (ej: -0.35 para -0.35%/°C).

IMPORTANTE: Si el documento NO es una ficha técnica de panel solar, indica confidence="low" y warnings=["El documento no parece ser una ficha técnica de panel solar"].`;

const EXTRACTION_JSON_SCHEMA = {
  name: "panel_parameters",
  strict: true,
  schema: {
    type: "object",
    properties: {
      name: { type: "string", description: "Nombre completo del panel (fabricante + modelo)" },
      manufacturer: { type: "string", description: "Fabricante del panel" },
      model: { type: "string", description: "Modelo/referencia del panel" },
      pmax: { type: ["number", "null"], description: "Potencia máxima STC en Watts" },
      voc: { type: ["number", "null"], description: "Voltaje circuito abierto STC en Volts" },
      isc: { type: ["number", "null"], description: "Corriente cortocircuito STC en Amperes" },
      vmp: { type: ["number", "null"], description: "Voltaje punto máxima potencia STC en Volts" },
      imp: { type: ["number", "null"], description: "Corriente punto máxima potencia STC en Amperes" },
      efficiencySTC: { type: ["number", "null"], description: "Eficiencia del módulo en STC (%)" },
      tempCoeffPmax: { type: ["number", "null"], description: "Coeficiente temperatura Pmax (%/°C, negativo)" },
      tempCoeffVoc: { type: ["number", "null"], description: "Coeficiente temperatura Voc (%/°C)" },
      tempCoeffIsc: { type: ["number", "null"], description: "Coeficiente temperatura Isc (%/°C)" },
      lengthMm: { type: ["number", "null"], description: "Largo del módulo en mm" },
      widthMm: { type: ["number", "null"], description: "Ancho del módulo en mm" },
      weightKg: { type: ["number", "null"], description: "Peso del módulo en kg" },
      noct: { type: ["number", "null"], description: "NOCT en °C (típico 42-47)" },
      degradationAnnual: { type: ["number", "null"], description: "Degradación anual (%/año)" },
      cellType: { type: ["string", "null"], description: "Tipo de célula: mono-Si, poly-Si, CdTe, CIGS, a-Si, perovskite, HJT, TOPCon" },
      application: { type: ["string", "null"], description: "Aplicación recomendada (BIPV, rooftop, ground-mount, etc.)" },
      confidence: { type: "string", enum: ["high", "medium", "low"], description: "Confianza de la extracción" },
      warnings: { type: "array", items: { type: "string" }, description: "Advertencias sobre datos faltantes o ambiguos" },
    },
    required: ["name", "manufacturer", "model", "pmax", "voc", "isc", "vmp", "imp", "efficiencySTC", "tempCoeffPmax", "tempCoeffVoc", "tempCoeffIsc", "lengthMm", "widthMm", "weightKg", "noct", "degradationAnnual", "cellType", "application", "confidence", "warnings"],
    additionalProperties: false,
  },
};

/**
 * Sube un PDF a storage y extrae parámetros de panel usando LLM con visión de documentos.
 */
export async function extractPanelFromPDF(
  pdfBuffer: Buffer,
  fileName: string,
): Promise<ExtractedPanelParams> {
  // 1. Subir PDF a storage para obtener URL accesible
  const fileKey = `pdf-datasheets/${Date.now()}_${fileName.replace(/[^a-zA-Z0-9._-]/g, '_')}`;
  const { key } = await storagePut(fileKey, pdfBuffer, 'application/pdf');

  // 2. Obtener URL firmada para que el LLM pueda acceder al PDF
  const signedUrl = await storageGetSignedUrl(key);

  // 3. Invocar LLM con el PDF como file_url
  const response = await invokeLLM({
    messages: [
      {
        role: "system",
        content: EXTRACTION_SYSTEM_PROMPT,
      },
      {
        role: "user",
        content: [
          {
            type: "file_url",
            file_url: {
              url: signedUrl,
              mime_type: "application/pdf",
            },
          },
          {
            type: "text",
            text: `Extrae los parámetros técnicos de esta ficha técnica de panel solar. El archivo se llama "${fileName}". Devuelve un JSON con todos los campos especificados.`,
          },
        ],
      },
    ],
    response_format: {
      type: "json_schema",
      json_schema: EXTRACTION_JSON_SCHEMA,
    },
  });

  // 4. Parsear respuesta
  const content = response.choices[0]?.message?.content;
  if (!content || typeof content !== 'string') {
    throw new Error('LLM no devolvió contenido válido');
  }

  const parsed = JSON.parse(content) as ExtractedPanelParams;

  // 5. Validaciones básicas y correcciones
  if (parsed.tempCoeffPmax !== null && parsed.tempCoeffPmax > 0) {
    // El coeficiente de Pmax siempre es negativo
    parsed.tempCoeffPmax = -Math.abs(parsed.tempCoeffPmax);
  }

  if (parsed.efficiencySTC !== null && parsed.efficiencySTC > 1 && parsed.efficiencySTC <= 100) {
    // Ya está en %, correcto
  } else if (parsed.efficiencySTC !== null && parsed.efficiencySTC <= 1) {
    // Está en fracción, convertir a %
    parsed.efficiencySTC = parsed.efficiencySTC * 100;
  }

  if (parsed.noct === null) {
    // Default NOCT según tipo de célula
    parsed.noct = parsed.cellType === 'CdTe' || parsed.cellType === 'a-Si' ? 46 : 45;
    parsed.warnings.push('NOCT no encontrado en el documento, se usó valor por defecto.');
  }

  if (parsed.degradationAnnual === null) {
    parsed.degradationAnnual = 0.55; // Default conservador
    parsed.warnings.push('Degradación anual no encontrada, se usó 0.55%/año por defecto.');
  }

  return parsed;
}
