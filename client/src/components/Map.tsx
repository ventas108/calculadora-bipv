/**
 * Map.tsx — Google Maps with Forge proxy + Leaflet/OpenStreetMap fallback
 *
 * This component provides a unified MapView that:
 * 1. Tries to load Google Maps via the Manus Forge proxy
 * 2. Falls back to Leaflet/OpenStreetMap if Google Maps is unavailable
 * 3. Provides a compatibility shim so existing components (IrradianceHeatmap,
 *    PVWattsSatellite, CityMapExplorer) work without modification
 *
 * CRITICAL FIX: Each MapView instance creates its own shim classes that target
 * its own Leaflet map instance. This prevents the singleton bug where all
 * overlays would render on the first map that was created.
 */

import { useRef, useState, useEffect, useCallback } from "react";
import { cn } from "@/lib/utils";

// Stable reference helper
function usePersistFn<T extends (...args: any[]) => any>(fn: T): T {
  const ref = useRef(fn);
  ref.current = fn;
  return useCallback((...args: any[]) => ref.current(...args), []) as any;
}

// ─── Configuration ────────────────────────────────────────────────────────────
const API_KEY = import.meta.env.VITE_FRONTEND_FORGE_API_KEY;
const FORGE_BASE_URL =
  import.meta.env.VITE_FRONTEND_FORGE_API_URL ||
  "https://forge.butterfly-effect.dev";
const MAPS_PROXY_URL = `${FORGE_BASE_URL}/v1/maps/proxy`;

// ─── Singleton script loader ────────────────────────────────────────────────
let _mapScriptPromise: Promise<void> | null = null;
let _mapScriptFailed = false;

function loadMapScript(): Promise<void> {
  if (window.google?.maps) {
    return Promise.resolve();
  }
  if (_mapScriptFailed) {
    return Promise.reject(new Error("Google Maps script previously failed to load"));
  }
  if (_mapScriptPromise) {
    return _mapScriptPromise;
  }
  _mapScriptPromise = new Promise<void>((resolve, reject) => {
    const script = document.createElement("script");
    script.src = `${MAPS_PROXY_URL}/maps/api/js?key=${API_KEY}&v=weekly&libraries=marker,places,geocoding,geometry,visualization`;
    script.async = true;
    script.crossOrigin = "anonymous";
    script.onload = () => {
      resolve();
      script.remove();
    };
    script.onerror = () => {
      console.error("Failed to load Google Maps script from Forge proxy");
      _mapScriptPromise = null;
      _mapScriptFailed = true;
      script.remove();
      reject(new Error("Failed to load Google Maps script"));
    };
    document.head.appendChild(script);
  });
  return _mapScriptPromise;
}

// ─── Leaflet Fallback Loader ────────────────────────────────────────────────
let _leafletPromise: Promise<typeof import("leaflet")> | null = null;

function loadLeaflet(): Promise<typeof import("leaflet")> {
  if (_leafletPromise) return _leafletPromise;
  _leafletPromise = (async () => {
    if (!document.querySelector('link[href*="leaflet"]')) {
      const link = document.createElement("link");
      link.rel = "stylesheet";
      link.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
      document.head.appendChild(link);
    }
    const L = await import("leaflet");
    return L;
  })();
  return _leafletPromise;
}

// ─── Helper: resolve leafletMap from a shimMap or opts.map ──────────────────
function resolveLeafletMap(mapObj: any): import("leaflet").Map | null {
  if (!mapObj) return null;
  if (mapObj._leafletMap) return mapObj._leafletMap;
  return null;
}

// ─── Google Maps Adapter for Leaflet (per-instance shim) ────────────────────
// IMPORTANT: Unlike the previous singleton approach, this creates shim CLASSES
// that resolve the target Leaflet map from opts.map at construction time.
// This ensures overlays always render on the correct map instance.

function createGoogleMapsShim(L: typeof import("leaflet"), leafletMap: import("leaflet").Map) {
  const shimMap: any = {
    _leafletMap: leafletMap,
    _leafletInstance: L,
    _markers: [] as any[],
    _circles: [] as any[],
    _isLeafletShim: true,

    getCenter() {
      const c = leafletMap.getCenter();
      return { lat: () => c.lat, lng: () => c.lng };
    },
    getZoom() {
      return leafletMap.getZoom();
    },
    setCenter(latLng: any) {
      const lat = typeof latLng.lat === "function" ? latLng.lat() : latLng.lat;
      const lng = typeof latLng.lng === "function" ? latLng.lng() : latLng.lng;
      leafletMap.setView([lat, lng], leafletMap.getZoom());
    },
    setZoom(zoom: number) {
      leafletMap.setZoom(zoom);
    },
    panTo(latLng: any) {
      const lat = typeof latLng.lat === "function" ? latLng.lat() : latLng.lat;
      const lng = typeof latLng.lng === "function" ? latLng.lng() : latLng.lng;
      leafletMap.panTo([lat, lng]);
    },
    fitBounds(bounds: any, _padding?: any) {
      if (bounds._leafletBounds) {
        leafletMap.fitBounds(bounds._leafletBounds);
      }
    },
    addListener(event: string, handler: Function) {
      const leafletEvent = event === "click" ? "click" : event;
      leafletMap.on(leafletEvent, (e: any) => {
        handler({
          latLng: {
            lat: () => e.latlng.lat,
            lng: () => e.latlng.lng,
          },
        });
      });
      return { remove: () => leafletMap.off(leafletEvent) };
    },
  };

  // Ensure global google.maps namespace exists
  if (!window.google) {
    (window as any).google = { maps: {} };
  }
  const gmaps = (window as any).google.maps;

  // ─── LatLngBounds (safe to be singleton - stateless factory) ───────────────
  if (!gmaps.LatLngBounds) {
    gmaps.LatLngBounds = class {
      _bounds: import("leaflet").LatLngBounds;
      constructor() {
        this._bounds = L.latLngBounds([]);
      }
      get _leafletBounds() { return this._bounds; }
      extend(latLng: any) {
        const lat = typeof latLng.lat === "function" ? latLng.lat() : latLng.lat;
        const lng = typeof latLng.lng === "function" ? latLng.lng() : latLng.lng;
        this._bounds.extend([lat, lng]);
        return this;
      }
      isEmpty() { return !this._bounds.isValid(); }
    };
  }

  // ─── Circle shim (ALWAYS recreate - must resolve target map from opts.map) ─
  // We ALWAYS overwrite gmaps.Circle because each instance must add to the
  // correct leaflet map (resolved from opts.map._leafletMap).
  gmaps.Circle = class {
    _circle: import("leaflet").Circle | null = null;
    _targetMap: import("leaflet").Map | null = null;

    constructor(opts: any) {
      const center = opts.center;
      const lat = typeof center.lat === "function" ? center.lat() : center.lat;
      const lng = typeof center.lng === "function" ? center.lng() : center.lng;
      const radius = opts.radius || 1000;
      const color = opts.strokeColor || opts.fillColor || "#3388ff";
      const fillOpacity = opts.fillOpacity ?? 0.3;
      const interactive = opts.clickable !== false;

      this._circle = L.circle([lat, lng], {
        radius,
        color: opts.strokeColor || color,
        weight: opts.strokeWeight || 2,
        fillColor: opts.fillColor || color,
        fillOpacity,
        interactive,
      });

      // Resolve the correct Leaflet map from opts.map
      this._targetMap = resolveLeafletMap(opts.map) || leafletMap;

      if (opts.map && this._circle) {
        this._circle.addTo(this._targetMap);
      }
    }

    addListener(event: string, handler: Function) {
      if (this._circle) {
        this._circle.on(event, (e: any) => handler(e));
      }
      return { remove: () => this._circle?.off(event) };
    }

    setMap(map: any) {
      const targetLMap = resolveLeafletMap(map) || this._targetMap;
      if (map && this._circle && targetLMap) {
        this._circle.addTo(targetLMap);
        this._targetMap = targetLMap;
      } else if (!map && this._circle) {
        this._circle.remove();
      }
    }

    getCenter() {
      if (!this._circle) return { lat: () => 0, lng: () => 0 };
      const c = this._circle.getLatLng();
      return { lat: () => c.lat, lng: () => c.lng };
    }
  };

  // ─── InfoWindow shim ──────────────────────────────────────────────────────
  if (!gmaps.InfoWindow) {
    gmaps.InfoWindow = class {
      _popup: import("leaflet").Popup;
      constructor(opts?: any) {
        this._popup = L.popup({ closeButton: true });
        if (opts?.content) this._popup.setContent(opts.content);
      }
      setContent(content: string) { this._popup.setContent(content); }
      open(opts: any) {
        const anchor = opts?.anchor;
        if (anchor?._marker) {
          anchor._marker.bindPopup(this._popup).openPopup();
        }
      }
      close() { this._popup.remove(); }
    };
  }

  // ─── AdvancedMarkerElement shim (ALWAYS recreate - must resolve target map) ─
  if (!gmaps.marker) {
    gmaps.marker = {};
  }
  gmaps.marker.AdvancedMarkerElement = class {
    _marker: import("leaflet").Marker | null = null;
    _targetMap: import("leaflet").Map | null = null;
    position: any;
    title: string;
    _map: any;
    content: any;

    constructor(opts: any) {
      this.position = opts.position;
      this.title = opts.title || "";
      this._map = opts.map;
      this.content = opts.content;

      // Resolve the correct Leaflet map
      this._targetMap = resolveLeafletMap(opts.map) || leafletMap;

      const lat = typeof opts.position?.lat === "function" ? opts.position.lat() : opts.position?.lat;
      const lng = typeof opts.position?.lng === "function" ? opts.position.lng() : opts.position?.lng;

      if (lat != null && lng != null) {
        let icon: import("leaflet").Icon | import("leaflet").DivIcon | undefined;
        if (opts.content instanceof HTMLElement) {
          const htmlContent = opts.content.outerHTML;
          const textContent = opts.content.textContent || "";
          const estimatedWidth = Math.max(30, textContent.length * 8 + 16);
          icon = L.divIcon({
            className: "leaflet-custom-marker",
            html: htmlContent,
            iconSize: [estimatedWidth, 20],
            iconAnchor: [estimatedWidth / 2, 10],
          });
        } else {
          icon = L.icon({
            iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
            iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
            shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
            iconSize: [25, 41],
            iconAnchor: [12, 41],
            popupAnchor: [1, -34],
          });
        }

        this._marker = L.marker([lat, lng], { icon, title: this.title });
        if (opts.map && this._targetMap) {
          this._marker.addTo(this._targetMap);
        }
      }
    }

    addListener(event: string, handler: Function) {
      if (this._marker) {
        this._marker.on(event, (e: any) => handler(e));
      }
      return { remove: () => this._marker?.off(event) };
    }

    remove() {
      if (this._marker) {
        this._marker.remove();
      }
    }

    get map() {
      return this._map;
    }

    set map(newMap: any) {
      this._map = newMap;
      const targetLMap = resolveLeafletMap(newMap) || this._targetMap;
      if (newMap && this._marker && targetLMap) {
        this._marker.addTo(targetLMap);
        this._targetMap = targetLMap;
      } else if (!newMap && this._marker) {
        this._marker.remove();
      }
    }
  };

  // ─── Geocoder shim (Nominatim) ────────────────────────────────────────────
  if (!gmaps.Geocoder) {
    gmaps.Geocoder = class {
      async geocode(request: any, callback: Function) {
        try {
          const address = request.address || "";
          const resp = await fetch(
            `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(address)}&limit=1`,
            { headers: { "User-Agent": "SolarShadingCalculator/1.0" } }
          );
          const data = await resp.json();
          if (data.length > 0) {
            const result = {
              geometry: {
                location: {
                  lat: () => parseFloat(data[0].lat),
                  lng: () => parseFloat(data[0].lon),
                },
              },
              formatted_address: data[0].display_name,
            };
            callback([result], "OK");
          } else {
            callback(null, "ZERO_RESULTS");
          }
        } catch {
          callback(null, "ERROR");
        }
      }
    };
    gmaps.GeocoderStatus = { OK: "OK", ZERO_RESULTS: "ZERO_RESULTS" };
  }

  // MapMouseEvent shim
  if (!gmaps.MapMouseEvent) {
    gmaps.MapMouseEvent = class {};
  }

  // event.trigger shim
  if (!gmaps.event) {
    gmaps.event = {
      trigger: () => {},
      addListener: (instance: any, event: string, handler: Function) => {
        if (instance?.on) instance.on(event, handler);
        return { remove: () => instance?.off?.(event) };
      },
    };
  }

  return shimMap;
}

// ─── MapView Component ──────────────────────────────────────────────────────
interface MapViewProps {
  className?: string;
  initialCenter?: google.maps.LatLngLiteral;
  initialZoom?: number;
  onMapReady?: (map: google.maps.Map) => void;
}

export function MapView({
  className,
  initialCenter = { lat: 37.7749, lng: -122.4194 },
  initialZoom = 12,
  onMapReady,
}: MapViewProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<google.maps.Map | null>(null);
  const initialized = useRef(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [usingFallback, setUsingFallback] = useState(false);

  const initGoogleMaps = useCallback(async (): Promise<boolean> => {
    try {
      await loadMapScript();
      if (!mapContainer.current || !window.google?.maps) return false;
      map.current = new window.google.maps.Map(mapContainer.current, {
        zoom: initialZoom,
        center: initialCenter,
        mapTypeControl: true,
        fullscreenControl: true,
        zoomControl: true,
        streetViewControl: true,
        mapId: "DEMO_MAP_ID",
      });
      return true;
    } catch {
      return false;
    }
  }, [initialCenter, initialZoom]);

  const initLeafletFallback = useCallback(async (): Promise<boolean> => {
    try {
      const L = await loadLeaflet();
      if (!mapContainer.current) return false;

      const leafletMap = L.map(mapContainer.current, {
        center: [initialCenter.lat, initialCenter.lng],
        zoom: initialZoom,
        zoomControl: true,
      });

      // Add OpenStreetMap tile layer
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
        maxZoom: 19,
      }).addTo(leafletMap);

      // Create the Google Maps compatibility shim FOR THIS SPECIFIC MAP
      const shimMap = createGoogleMapsShim(L, leafletMap);
      map.current = shimMap as any;
      setUsingFallback(true);

      // Force resize after a short delay to ensure proper rendering
      setTimeout(() => leafletMap.invalidateSize(), 100);

      return true;
    } catch (err) {
      console.error("Leaflet fallback also failed:", err);
      return false;
    }
  }, [initialCenter, initialZoom]);

  const init = usePersistFn(async () => {
    if (initialized.current) return;
    setLoading(true);
    setError(null);

    // Try Google Maps first
    let success = await initGoogleMaps();

    // If Google Maps fails, use Leaflet fallback
    if (!success) {
      console.warn("Google Maps unavailable, using Leaflet/OpenStreetMap fallback");
      success = await initLeafletFallback();
    }

    if (success) {
      initialized.current = true;
      setLoading(false);
      if (onMapReady && map.current) {
        onMapReady(map.current);
      }
    } else {
      setError("No se pudo cargar el mapa. Verifica tu conexión a internet.");
      setLoading(false);
    }
  });

  useEffect(() => {
    init();
  }, [init]);

  // Trigger resize when container becomes visible again
  useEffect(() => {
    if (!map.current || !mapContainer.current) return;
    const observer = new ResizeObserver(() => {
      if ((map.current as any)?._leafletMap) {
        (map.current as any)._leafletMap.invalidateSize();
      } else if (window.google?.maps?.event && map.current) {
        window.google.maps.event.trigger(map.current, "resize");
      }
    });
    observer.observe(mapContainer.current);
    return () => observer.disconnect();
  }, [loading]);

  return (
    <div className={cn("relative w-full h-[500px]", className)}>
      {loading && !initialized.current && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-100 rounded-lg z-10">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
            <p className="text-sm text-gray-600">Cargando mapa...</p>
          </div>
        </div>
      )}
      {error && (
        <div className="absolute inset-0 flex items-center justify-center bg-red-50 rounded-lg z-10">
          <div className="text-center p-4">
            <p className="text-sm text-red-600 mb-2">{error}</p>
            <button
              onClick={() => {
                _mapScriptPromise = null;
                _mapScriptFailed = false;
                initialized.current = false;
                setError(null);
                init();
              }}
              className="px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700"
            >
              Reintentar
            </button>
          </div>
        </div>
      )}
      {usingFallback && !loading && (
        <div className="absolute top-2 right-2 z-[1000] bg-amber-100 text-amber-800 text-xs px-2 py-1 rounded shadow">
          OpenStreetMap (fallback)
        </div>
      )}
      <div ref={mapContainer} className="w-full h-full rounded-lg" />
    </div>
  );
}
