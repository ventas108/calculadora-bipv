/**
 * PVGIS Proxy - Backend endpoint para consultar PVGIS sin restricciones CORS
 * 
 * PVGIS (Photovoltaic Geographical Information System) de la Comisión Europea
 * no permite CORS desde frontends. Este proxy realiza las consultas desde el servidor.
 */

import type { Express, Request, Response } from 'express';

const PVGIS_BASE_URL = 'https://re.jrc.ec.europa.eu/api/v5_3';

// Endpoints permitidos de PVGIS
const ALLOWED_ENDPOINTS = ['MRcalc', 'PVcalc', 'seriescalc', 'printhorizon', 'tmy'];

// Parámetros permitidos para evitar abuso
const ALLOWED_PARAMS = [
  'lat', 'lon', 'outputformat', 'raddatabase',
  'horirrad', 'optrad', 'mr_dni', 'd2g', 'avtemp', 'selectrad', 'angle', 'aspect',
  'peakpower', 'loss', 'optimalangles', 'optimalinclination',
  'startyear', 'endyear', 'pvcalculation', 'pvtechchoice',
  'mountingplace', 'fixed', 'inclined_axis', 'vertical_axis', 'twoaxis',
  'usehorizon', 'userhorizon',
  'components',  // 1 = return Gb(i), Gd(i), Gr(i) instead of G(i)
];

export function registerPVGISProxy(app: Express) {
  // Endpoint principal: /api/pvgis/:endpoint
  app.get('/api/pvgis/:endpoint', async (req: Request, res: Response) => {
    try {
      const { endpoint } = req.params;

      // Validar endpoint
      if (!ALLOWED_ENDPOINTS.includes(endpoint)) {
        res.status(400).json({
          error: `Endpoint no permitido: ${endpoint}`,
          allowed: ALLOWED_ENDPOINTS,
        });
        return;
      }

      // Filtrar y construir parámetros
      const params = new URLSearchParams();
      for (const [key, value] of Object.entries(req.query)) {
        if (ALLOWED_PARAMS.includes(key) && typeof value === 'string') {
          params.append(key, value);
        }
      }

      // Asegurar formato JSON
      params.set('outputformat', 'json');

      const pvgisUrl = `${PVGIS_BASE_URL}/${endpoint}?${params.toString()}`;
      
      console.log(`[PVGIS Proxy] Fetching: ${pvgisUrl}`);

      const response = await fetch(pvgisUrl, {
        headers: {
          'Accept': 'application/json',
          'User-Agent': 'SolarShadingCalculator/1.0',
        },
        signal: AbortSignal.timeout(60000), // 60 second timeout (seriescalc can be slow)
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error(`[PVGIS Proxy] Error ${response.status}: ${errorText}`);
        res.status(response.status).json({
          error: `PVGIS respondió con error ${response.status}`,
          details: errorText,
        });
        return;
      }

      const data = await response.json();
      
      // Cache headers para reducir llamadas repetidas
      res.setHeader('Cache-Control', 'public, max-age=86400'); // 24 horas
      res.json(data);
    } catch (error: any) {
      console.error('[PVGIS Proxy] Error:', error.message);
      
      if (error.name === 'TimeoutError' || error.name === 'AbortError') {
        res.status(504).json({
          error: 'Timeout: PVGIS no respondió en 30 segundos. Intenta de nuevo.',
        });
        return;
      }

      res.status(500).json({
        error: 'Error interno al consultar PVGIS',
        details: error.message,
      });
    }
  });

  console.log('[PVGIS Proxy] Registered at /api/pvgis/:endpoint');
}
