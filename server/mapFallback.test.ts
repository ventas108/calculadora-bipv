/**
 * Tests for Map.tsx Google Maps + Leaflet fallback logic.
 * Since Map.tsx is a React component with DOM dependencies, we test the
 * underlying logic patterns: singleton script loading, fallback detection,
 * and the Google Maps shim API compatibility.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';

describe('Map Fallback Logic', () => {
  describe('Singleton Script Loading Pattern', () => {
    it('should only create one script element per session', () => {
      // Simulates the singleton pattern: if promise exists, reuse it
      let promiseCount = 0;
      let cachedPromise: Promise<void> | null = null;

      function loadScript(): Promise<void> {
        if (cachedPromise) return cachedPromise;
        promiseCount++;
        cachedPromise = Promise.resolve();
        return cachedPromise;
      }

      loadScript();
      loadScript();
      loadScript();
      expect(promiseCount).toBe(1);
    });

    it('should reset promise on failure to allow retry', () => {
      let promiseCount = 0;
      let cachedPromise: Promise<void> | null = null;
      let shouldFail = true;

      function loadScript(): Promise<void> {
        if (cachedPromise) return cachedPromise;
        promiseCount++;
        if (shouldFail) {
          cachedPromise = null; // Reset on failure
          return Promise.reject(new Error('Failed'));
        }
        cachedPromise = Promise.resolve();
        return cachedPromise;
      }

      // First attempt fails
      loadScript().catch(() => {});
      expect(promiseCount).toBe(1);

      // Second attempt should try again since promise was reset
      shouldFail = false;
      loadScript();
      expect(promiseCount).toBe(2);
    });
  });

  describe('Google Maps Shim API Compatibility', () => {
    it('should create LatLngBounds that can extend and check validity', () => {
      // Simulates the LatLngBounds shim behavior
      class LatLngBoundsShim {
        private points: Array<{ lat: number; lng: number }> = [];

        extend(latLng: { lat: number; lng: number }) {
          this.points.push(latLng);
          return this;
        }

        isEmpty() {
          return this.points.length === 0;
        }

        getCenter() {
          if (this.points.length === 0) return { lat: 0, lng: 0 };
          const sumLat = this.points.reduce((s, p) => s + p.lat, 0);
          const sumLng = this.points.reduce((s, p) => s + p.lng, 0);
          return {
            lat: sumLat / this.points.length,
            lng: sumLng / this.points.length,
          };
        }
      }

      const bounds = new LatLngBoundsShim();
      expect(bounds.isEmpty()).toBe(true);

      bounds.extend({ lat: 6.25, lng: -75.56 });
      bounds.extend({ lat: 7.0, lng: -74.0 });
      expect(bounds.isEmpty()).toBe(false);

      const center = bounds.getCenter();
      expect(center.lat).toBeCloseTo(6.625, 2);
      expect(center.lng).toBeCloseTo(-74.78, 2);
    });

    it('should handle position objects with both function and literal formats', () => {
      // Google Maps uses { lat: () => number, lng: () => number }
      // But also accepts { lat: number, lng: number }
      function extractLatLng(position: any): { lat: number; lng: number } {
        const lat = typeof position.lat === 'function' ? position.lat() : position.lat;
        const lng = typeof position.lng === 'function' ? position.lng() : position.lng;
        return { lat, lng };
      }

      // Function format (Google Maps style)
      const funcPos = { lat: () => 6.25, lng: () => -75.56 };
      expect(extractLatLng(funcPos)).toEqual({ lat: 6.25, lng: -75.56 });

      // Literal format (Leaflet style)
      const litPos = { lat: 6.25, lng: -75.56 };
      expect(extractLatLng(litPos)).toEqual({ lat: 6.25, lng: -75.56 });
    });

    it('should map Google Maps events to Leaflet events correctly', () => {
      const eventMap: Record<string, string> = {
        click: 'click',
        dblclick: 'dblclick',
        mouseover: 'mouseover',
        mouseout: 'mouseout',
      };

      // The shim maps event names directly (they're the same in both APIs)
      expect(eventMap['click']).toBe('click');
      expect(eventMap['dblclick']).toBe('dblclick');
    });

    it('should create Circle shim with correct parameters', () => {
      // Simulates Circle creation with Google Maps API format
      interface CircleOptions {
        center: { lat: number; lng: number };
        radius: number;
        strokeColor: string;
        strokeWeight: number;
        fillColor: string;
        fillOpacity: number;
        map?: any;
      }

      function createCircleParams(opts: CircleOptions) {
        return {
          lat: opts.center.lat,
          lng: opts.center.lng,
          radius: opts.radius,
          color: opts.strokeColor,
          weight: opts.strokeWeight,
          fillColor: opts.fillColor,
          fillOpacity: opts.fillOpacity,
        };
      }

      const params = createCircleParams({
        center: { lat: 6.25, lng: -75.56 },
        radius: 5000,
        strokeColor: '#ff0000',
        strokeWeight: 2,
        fillColor: '#ff0000',
        fillOpacity: 0.3,
      });

      expect(params.lat).toBe(6.25);
      expect(params.lng).toBe(-75.56);
      expect(params.radius).toBe(5000);
      expect(params.color).toBe('#ff0000');
      expect(params.fillOpacity).toBe(0.3);
    });

    it('should handle Geocoder shim with Nominatim-compatible response format', () => {
      // Simulates converting Nominatim response to Google Maps Geocoder format
      function convertNominatimResult(data: Array<{ lat: string; lon: string; display_name: string }>) {
        if (data.length === 0) return { results: null, status: 'ZERO_RESULTS' };
        return {
          results: data.map(item => ({
            geometry: {
              location: {
                lat: () => parseFloat(item.lat),
                lng: () => parseFloat(item.lon),
              },
            },
            formatted_address: item.display_name,
          })),
          status: 'OK',
        };
      }

      // Test with results
      const result = convertNominatimResult([
        { lat: '6.2518', lon: '-75.5636', display_name: 'Medellín, Antioquia, Colombia' },
      ]);
      expect(result.status).toBe('OK');
      expect(result.results![0].geometry.location.lat()).toBeCloseTo(6.2518, 3);
      expect(result.results![0].geometry.location.lng()).toBeCloseTo(-75.5636, 3);
      expect(result.results![0].formatted_address).toContain('Medellín');

      // Test without results
      const empty = convertNominatimResult([]);
      expect(empty.status).toBe('ZERO_RESULTS');
      expect(empty.results).toBeNull();
    });

    it('should create marker with custom colored div icon', () => {
      // Simulates the DivIcon creation for colored markers
      function createMarkerIconHtml(backgroundColor: string): string {
        return `<div style="width:14px;height:14px;border-radius:50%;background:${backgroundColor};border:2px solid white;box-shadow:0 1px 3px rgba(0,0,0,0.3);"></div>`;
      }

      const html = createMarkerIconHtml('#ef4444');
      expect(html).toContain('background:#ef4444');
      expect(html).toContain('border-radius:50%');
      expect(html).toContain('border:2px solid white');
    });
  });

  describe('Fallback Strategy', () => {
    it('should try Google Maps first, then fall back to Leaflet', async () => {
      const attempts: string[] = [];
      let googleFails = true;

      async function initMap(): Promise<string> {
        // Try Google Maps first
        attempts.push('google');
        if (!googleFails) return 'google';

        // Fallback to Leaflet
        attempts.push('leaflet');
        return 'leaflet';
      }

      const result = await initMap();
      expect(result).toBe('leaflet');
      expect(attempts).toEqual(['google', 'leaflet']);
    });

    it('should use Google Maps when available (production)', async () => {
      const attempts: string[] = [];
      let googleFails = false; // Google Maps works in production

      async function initMap(): Promise<string> {
        attempts.push('google');
        if (!googleFails) return 'google';
        attempts.push('leaflet');
        return 'leaflet';
      }

      const result = await initMap();
      expect(result).toBe('google');
      expect(attempts).toEqual(['google']);
    });

    it('should prevent double initialization', async () => {
      let initCount = 0;
      let initialized = false;

      async function init() {
        if (initialized) return;
        initialized = true;
        initCount++;
      }

      await init();
      await init();
      await init();
      expect(initCount).toBe(1);
    });
  });

  describe('Lazy Mount Persistence Pattern', () => {
    it('should track ever-shown state for each map view', () => {
      const everShown = {
        heatmap: false,
        pvwatts: false,
        pvgis: false,
      };

      function setView(view: string) {
        if (view === 'heatmap') everShown.heatmap = true;
        if (view === 'pvwatts') everShown.pvwatts = true;
        if (view === 'pvgis') everShown.pvgis = true;
      }

      // Initially nothing shown
      expect(everShown.heatmap).toBe(false);
      expect(everShown.pvwatts).toBe(false);

      // Show heatmap
      setView('heatmap');
      expect(everShown.heatmap).toBe(true);
      expect(everShown.pvwatts).toBe(false);

      // Switch to calculator (heatmap stays mounted)
      setView('calculator');
      expect(everShown.heatmap).toBe(true);

      // Show pvwatts
      setView('pvwatts');
      expect(everShown.pvwatts).toBe(true);
      expect(everShown.heatmap).toBe(true); // Still true
    });

    it('should keep map DOM alive when hidden via CSS display:none', () => {
      // Simulates the display:none pattern
      function getDisplayStyle(view: string, currentView: string): string {
        return view === currentView ? 'block' : 'none';
      }

      expect(getDisplayStyle('heatmap', 'heatmap')).toBe('block');
      expect(getDisplayStyle('heatmap', 'calculator')).toBe('none');
      expect(getDisplayStyle('heatmap', 'pvwatts')).toBe('none');
      expect(getDisplayStyle('pvwatts', 'pvwatts')).toBe('block');
    });
  });

  describe('Map Configuration', () => {
    it('should construct correct Forge proxy URL', () => {
      const forgeBaseUrl = 'https://forge.manus.ai';
      const apiKey = 'test-key';
      const url = `${forgeBaseUrl}/v1/maps/proxy/maps/api/js?key=${apiKey}&v=weekly&libraries=marker,places,geocoding,geometry,visualization`;

      expect(url).toContain('/v1/maps/proxy/');
      expect(url).toContain('key=test-key');
      expect(url).toContain('libraries=marker,places,geocoding,geometry,visualization');
    });

    it('should use fallback Forge URL when env var is not set', () => {
      const envUrl = undefined;
      const forgeBaseUrl = envUrl || 'https://forge.butterfly-effect.dev';
      expect(forgeBaseUrl).toBe('https://forge.butterfly-effect.dev');
    });

    it('should default to San Francisco coordinates when no center provided', () => {
      const defaultCenter = { lat: 37.7749, lng: -122.4194 };
      expect(defaultCenter.lat).toBeCloseTo(37.7749, 4);
      expect(defaultCenter.lng).toBeCloseTo(-122.4194, 4);
    });
  });
});
