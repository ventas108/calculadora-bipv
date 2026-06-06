import { describe, it, expect, vi } from 'vitest';

// Mock del módulo LLM
vi.mock('./_core/llm', () => ({
  invokeLLM: vi.fn(),
}));

// Mock del módulo storage
vi.mock('./storage', () => ({
  storagePut: vi.fn().mockResolvedValue({ key: 'pdf-datasheets/test.pdf', url: '/manus-storage/pdf-datasheets/test.pdf' }),
  storageGetSignedUrl: vi.fn().mockResolvedValue('https://signed-url.example.com/test.pdf'),
}));

import { extractPanelFromPDF } from './pdfPanelExtractor';
import { invokeLLM } from './_core/llm';

const mockLLMResponse = {
  id: 'test-id',
  created: Date.now(),
  model: 'test-model',
  choices: [{
    index: 0,
    message: {
      role: 'assistant' as const,
      content: JSON.stringify({
        name: 'JA Solar JAM72S30-550/MR',
        manufacturer: 'JA Solar',
        model: 'JAM72S30-550/MR',
        pmax: 550,
        voc: 49.65,
        isc: 13.98,
        vmp: 41.82,
        imp: 13.15,
        efficiencySTC: 21.3,
        tempCoeffPmax: -0.35,
        tempCoeffVoc: -0.27,
        tempCoeffIsc: 0.048,
        lengthMm: 2278,
        widthMm: 1134,
        weightKg: 28.9,
        noct: 45,
        degradationAnnual: 0.55,
        cellType: 'mono-Si',
        application: 'rooftop, ground-mount',
        confidence: 'high',
        warnings: [],
      }),
    },
    finish_reason: 'stop',
  }],
};

describe('PDF Panel Extractor', () => {
  it('should extract panel parameters from a PDF buffer', async () => {
    (invokeLLM as any).mockResolvedValue(mockLLMResponse);

    const fakeBuffer = Buffer.from('fake pdf content');
    const result = await extractPanelFromPDF(fakeBuffer, 'JA_Solar_550W.pdf');

    expect(result.name).toBe('JA Solar JAM72S30-550/MR');
    expect(result.manufacturer).toBe('JA Solar');
    expect(result.model).toBe('JAM72S30-550/MR');
    expect(result.pmax).toBe(550);
    expect(result.voc).toBe(49.65);
    expect(result.isc).toBe(13.98);
    expect(result.vmp).toBe(41.82);
    expect(result.imp).toBe(13.15);
    expect(result.efficiencySTC).toBe(21.3);
    expect(result.tempCoeffPmax).toBe(-0.35);
    expect(result.noct).toBe(45);
    expect(result.cellType).toBe('mono-Si');
    expect(result.confidence).toBe('high');
    expect(result.warnings).toHaveLength(0);
  });

  it('should correct positive tempCoeffPmax to negative', async () => {
    const responseWithPositiveCoeff = {
      ...mockLLMResponse,
      choices: [{
        ...mockLLMResponse.choices[0],
        message: {
          ...mockLLMResponse.choices[0].message,
          content: JSON.stringify({
            name: 'Test Panel',
            manufacturer: 'Test',
            model: 'TP-400',
            pmax: 400,
            voc: 40,
            isc: 10,
            vmp: 33,
            imp: 9.5,
            efficiencySTC: 20.5,
            tempCoeffPmax: 0.35, // Positivo (error común en extracción)
            tempCoeffVoc: -0.27,
            tempCoeffIsc: 0.048,
            lengthMm: 1700,
            widthMm: 1000,
            weightKg: 22,
            noct: null, // No encontrado
            degradationAnnual: null, // No encontrado
            cellType: 'mono-Si',
            application: null,
            confidence: 'medium',
            warnings: ['Algunos valores estimados'],
          }),
        },
      }],
    };

    (invokeLLM as any).mockResolvedValue(responseWithPositiveCoeff);

    const fakeBuffer = Buffer.from('fake pdf content');
    const result = await extractPanelFromPDF(fakeBuffer, 'test.pdf');

    // tempCoeffPmax debe ser negativo
    expect(result.tempCoeffPmax).toBe(-0.35);
    // NOCT debe tener valor por defecto
    expect(result.noct).toBe(45);
    // Degradación debe tener valor por defecto
    expect(result.degradationAnnual).toBe(0.55);
    // Debe tener warnings adicionales
    expect(result.warnings.length).toBeGreaterThan(1);
    expect(result.warnings).toContain('NOCT no encontrado en el documento, se usó valor por defecto.');
    expect(result.warnings).toContain('Degradación anual no encontrada, se usó 0.55%/año por defecto.');
  });

  it('should convert efficiency from fraction to percentage', async () => {
    const responseWithFractionEff = {
      ...mockLLMResponse,
      choices: [{
        ...mockLLMResponse.choices[0],
        message: {
          ...mockLLMResponse.choices[0].message,
          content: JSON.stringify({
            name: 'Test Panel Fraction',
            manufacturer: 'Test',
            model: 'TP-300',
            pmax: 300,
            voc: 38,
            isc: 9,
            vmp: 32,
            imp: 8.5,
            efficiencySTC: 0.195, // En fracción en vez de %
            tempCoeffPmax: -0.40,
            tempCoeffVoc: -0.30,
            tempCoeffIsc: 0.05,
            lengthMm: 1650,
            widthMm: 990,
            weightKg: 20,
            noct: 43,
            degradationAnnual: 0.7,
            cellType: 'poly-Si',
            application: 'rooftop',
            confidence: 'high',
            warnings: [],
          }),
        },
      }],
    };

    (invokeLLM as any).mockResolvedValue(responseWithFractionEff);

    const fakeBuffer = Buffer.from('fake pdf content');
    const result = await extractPanelFromPDF(fakeBuffer, 'test_fraction.pdf');

    // Debe convertir 0.195 → 19.5%
    expect(result.efficiencySTC).toBe(19.5);
  });

  it('should handle CdTe panels with appropriate NOCT default', async () => {
    const cdteResponse = {
      ...mockLLMResponse,
      choices: [{
        ...mockLLMResponse.choices[0],
        message: {
          ...mockLLMResponse.choices[0].message,
          content: JSON.stringify({
            name: 'First Solar Series 6 Plus',
            manufacturer: 'First Solar',
            model: 'FS-6450',
            pmax: 450,
            voc: 219.6,
            isc: 2.61,
            vmp: 185.4,
            imp: 2.43,
            efficiencySTC: 18.4,
            tempCoeffPmax: -0.28,
            tempCoeffVoc: -0.28,
            tempCoeffIsc: 0.04,
            lengthMm: 2009,
            widthMm: 1232,
            weightKg: 32.2,
            noct: null,
            degradationAnnual: 0.5,
            cellType: 'CdTe',
            application: 'utility-scale',
            confidence: 'high',
            warnings: [],
          }),
        },
      }],
    };

    (invokeLLM as any).mockResolvedValue(cdteResponse);

    const fakeBuffer = Buffer.from('fake pdf content');
    const result = await extractPanelFromPDF(fakeBuffer, 'first_solar.pdf');

    // CdTe debe tener NOCT = 46 por defecto
    expect(result.noct).toBe(46);
    expect(result.cellType).toBe('CdTe');
  });

  it('should throw on LLM failure', async () => {
    (invokeLLM as any).mockResolvedValue({
      choices: [{
        index: 0,
        message: { role: 'assistant', content: null },
        finish_reason: 'stop',
      }],
    });

    const fakeBuffer = Buffer.from('fake pdf content');
    await expect(extractPanelFromPDF(fakeBuffer, 'bad.pdf')).rejects.toThrow('LLM no devolvió contenido válido');
  });
});
