/**
 * PVWatts Proxy - Backend endpoint para consultar PVWatts v8 de NREL sin restricciones CORS
 * 
 * PVWatts (NREL) proporciona estimaciones de producción solar basadas en datos satelitales TMY.
 * La API requiere una API key gratuita de NREL.
 * 
 * Documentación: https://developer.nlr.gov/docs/solar/pvwatts/v8/
 */

import type { Express, Request, Response } from 'express';

const PVWATTS_BASE_URL = 'https://developer.nlr.gov/api/pvwatts/v8.json';

// Parámetros permitidos para PVWatts v8
const ALLOWED_PARAMS = [
  'lat', 'lon',
  'system_capacity',   // kW DC nameplate
  'azimuth',           // 0-360 degrees
  'tilt',              // 0-90 degrees
  'array_type',        // 0=Fixed Open Rack, 1=Fixed Roof Mount, 2=1-Axis, 3=1-Axis Backtracking, 4=2-Axis
  'module_type',       // 0=Standard, 1=Premium, 2=Thin Film
  'losses',            // System losses (%)
  'timeframe',         // monthly or hourly
  'dataset',           // nsrdb, intl, tmy2, tmy3
  'radius',            // Search radius for closest station (miles)
  'dc_ac_ratio',       // DC to AC ratio
  'gcr',               // Ground coverage ratio
  'inv_eff',           // Inverter efficiency (%)
  'bifaciality',       // Bifaciality factor
  'albedo',            // Ground albedo
];

interface CacheEntry {
  data: any;
  timestamp: number;
}

const pvwattsCache = new Map<string, CacheEntry>();
const CACHE_TTL = 24 * 60 * 60 * 1000; // 24 horas

export function registerPVWattsProxy(app: Express) {
  // Endpoint principal: /api/pvwatts
  app.get('/api/pvwatts', async (req: Request, res: Response) => {
    let cacheKey = '';
    try {
      const lat = req.query.lat;
      const lon = req.query.lon;
      const system_capacity = req.query.system_capacity || '1';
      const azimuth = req.query.azimuth || '180';
      const tilt = req.query.tilt || '10';
      const losses = req.query.losses || '14';
      const timeframe = req.query.timeframe || 'monthly';
      const dataset = req.query.dataset || 'default';

      if (typeof lat === 'string' && typeof lon === 'string') {
        const latRounded = parseFloat(lat).toFixed(3);
        const lonRounded = parseFloat(lon).toFixed(3);
        cacheKey = `${latRounded}_${lonRounded}_${system_capacity}_${azimuth}_${tilt}_${losses}_${timeframe}_${dataset}`;

        const cached = pvwattsCache.get(cacheKey);
        if (cached && (Date.now() - cached.timestamp < CACHE_TTL)) {
          console.log(`[PVWatts Proxy] Cache HIT for key: ${cacheKey}`);
          res.setHeader('Cache-Control', 'public, max-age=86400');
          res.setHeader('X-Cache', 'HIT');
          res.json(cached.data);
          return;
        }
      }

      let apiKey = process.env.NREL_API_KEY;
      if (!apiKey) {
        console.warn('[PVWatts Proxy] WARNING: NREL_API_KEY is not set. Falling back to DEMO_KEY.');
        apiKey = 'DEMO_KEY';
      }

      // Filtrar y construir parámetros
      const params = new URLSearchParams();
      params.set('api_key', apiKey);

      for (const [key, value] of Object.entries(req.query)) {
        if (ALLOWED_PARAMS.includes(key) && typeof value === 'string') {
          params.append(key, value);
        }
      }

      // Asegurar timeframe monthly por defecto
      if (!params.has('timeframe')) {
        params.set('timeframe', 'monthly');
      }

      const pvwattsUrl = `${PVWATTS_BASE_URL}?${params.toString()}`;

      console.log(`[PVWatts Proxy] Fetching: ${PVWATTS_BASE_URL}?lat=${params.get('lat')}&lon=${params.get('lon')}&...`);

      const response = await fetch(pvwattsUrl, {
        headers: {
          'Accept': 'application/json',
          'User-Agent': 'SolarShadingCalculator/1.0',
        },
        signal: AbortSignal.timeout(60000), // 60 second timeout (hourly data can be large)
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error(`[PVWatts Proxy] Error ${response.status}: ${errorText}`);
        res.status(response.status).json({
          error: `PVWatts respondió con error ${response.status}`,
          details: errorText,
        });
        return;
      }

      const data = await response.json();

      // Verificar si hay errores en la respuesta de NREL
      if (data.errors && data.errors.length > 0) {
        res.status(422).json({
          error: 'PVWatts reportó errores en la consulta',
          details: data.errors,
        });
        return;
      }

      // Guardar en la caché en memoria
      if (cacheKey) {
        // Evitar crecimiento infinito de la memoria
        if (pvwattsCache.size > 1000) {
          const now = Date.now();
          for (const [k, v] of pvwattsCache.entries()) {
            if (now - v.timestamp > CACHE_TTL) {
              pvwattsCache.delete(k);
            }
          }
          if (pvwattsCache.size > 1000) {
            pvwattsCache.clear();
          }
        }
        pvwattsCache.set(cacheKey, {
          data,
          timestamp: Date.now(),
        });
        console.log(`[PVWatts Proxy] Cache STORED for key: ${cacheKey} (Total: ${pvwattsCache.size})`);
      }

      // Cache headers para reducir llamadas repetidas
      res.setHeader('Cache-Control', 'public, max-age=86400'); // 24 horas
      res.json(data);
    } catch (error: any) {
      console.error('[PVWatts Proxy] Error:', error.message);

      if (error.name === 'TimeoutError' || error.name === 'AbortError') {
        res.status(504).json({
          error: 'Timeout: PVWatts no respondió en 30 segundos. Intenta de nuevo.',
        });
        return;
      }

      res.status(500).json({
        error: 'Error interno al consultar PVWatts',
        details: error.message,
      });
    }
  });

  console.log('[PVWatts Proxy] Registered at /api/pvwatts');
}
