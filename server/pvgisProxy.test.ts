/**
 * Cobertura real de server/pvgisProxy.ts (CodeSpecs/02-recurso-solar/react,
 * tarea #6). El nombre de archivo ya lo tenía tomado una suite que en
 * realidad probaba client/src/lib/irradianceHeatmap.ts (librería sintética
 * sin consumidor real) -- se movió a server/irradianceHeatmapSynthetic.test.ts
 * sin cambiar su contenido.
 *
 * Se levanta el Express real de registerPVGISProxy() en un puerto efímero y
 * se mockea `global.fetch` (la única llamada de red que hace el proxy, hacia
 * PVGIS) -- el fetch real de Node se preserva aparte para que el propio test
 * pueda llamar al servidor local sin quedar interceptado por el mock.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import express, { type Express } from "express";
import type { Server } from "http";
import { registerPVGISProxy } from "./pvgisProxy";

const realFetch = global.fetch;

async function startTestServer(): Promise<{ server: Server; baseUrl: string }> {
  const app: Express = express();
  registerPVGISProxy(app);
  return new Promise((resolve) => {
    const server = app.listen(0, () => {
      const address = server.address();
      const port = typeof address === "object" && address ? address.port : 0;
      resolve({ server, baseUrl: `http://127.0.0.1:${port}` });
    });
  });
}

describe("server/pvgisProxy.ts", () => {
  let server: Server;
  let baseUrl: string;
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(async () => {
    ({ server, baseUrl } = await startTestServer());
    fetchMock = vi.fn();
    // @ts-expect-error -- stub deliberado, solo para la llamada saliente del proxy
    global.fetch = fetchMock;
  });

  afterEach(async () => {
    global.fetch = realFetch;
    await new Promise<void>((resolve) => server.close(() => resolve()));
  });

  it("rechaza un endpoint no permitido con 400", async () => {
    const res = await realFetch(`${baseUrl}/api/pvgis/endpointInventado`);
    expect(res.status).toBe(400);
    const body = await res.json();
    expect(body.error).toContain("no permitido");
    expect(body.allowed).toContain("PVcalc");
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("filtra parámetros no permitidos y fuerza outputformat=json", async () => {
    fetchMock.mockResolvedValue(new Response(JSON.stringify({ ok: true }), { status: 200 }));
    await realFetch(
      `${baseUrl}/api/pvgis/PVcalc?lat=4.6&lon=-74.1&peakpower=1&loss=14&evilParam=1&outputformat=xml`,
    );
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const calledUrl = fetchMock.mock.calls[0][0] as string;
    expect(calledUrl.startsWith("https://re.jrc.ec.europa.eu/api/v5_3/PVcalc?")).toBe(true);
    expect(calledUrl).toContain("lat=4.6");
    expect(calledUrl).toContain("peakpower=1");
    expect(calledUrl).not.toContain("evilParam");
    expect(calledUrl).toContain("outputformat=json");
    expect(calledUrl).not.toContain("xml");
  });

  it("responde 200 con los datos de PVGIS y cabecera de cache", async () => {
    fetchMock.mockResolvedValue(new Response(JSON.stringify({ outputs: { hi: 1 } }), { status: 200 }));
    const res = await realFetch(`${baseUrl}/api/pvgis/MRcalc?lat=4.6&lon=-74.1`);
    expect(res.status).toBe(200);
    expect(res.headers.get("cache-control")).toContain("max-age=86400");
    expect(await res.json()).toEqual({ outputs: { hi: 1 } });
  });

  it("propaga el código y el cuerpo de error cuando PVGIS responde con un error HTTP", async () => {
    fetchMock.mockResolvedValue(new Response("Not found. Please, revise the function call.", { status: 404 }));
    const res = await realFetch(`${baseUrl}/api/pvgis/MRcalc?lat=4.6&lon=-74.1`);
    expect(res.status).toBe(404);
    const body = await res.json();
    expect(body.error).toContain("404");
    expect(body.details).toContain("revise the function call");
  });

  it("reintenta ante un fallo de red transitorio (ECONNRESET) y responde 200 si el reintento tiene éxito", async () => {
    fetchMock
      .mockRejectedValueOnce(Object.assign(new Error("fetch failed"), { cause: { code: "ECONNRESET" } }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ ok: true }), { status: 200 }));
    const res = await realFetch(`${baseUrl}/api/pvgis/MRcalc?lat=4.6&lon=-74.1`);
    expect(res.status).toBe(200);
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("responde 500 si el fallo de red persiste en todos los reintentos", async () => {
    fetchMock.mockRejectedValue(Object.assign(new Error("fetch failed"), { cause: { code: "ECONNRESET" } }));
    const res = await realFetch(`${baseUrl}/api/pvgis/MRcalc?lat=4.6&lon=-74.1`);
    expect(res.status).toBe(500);
    // retries=2 en fetchWithRetry -> 1 intento inicial + 2 reintentos = 3 llamadas.
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });
});
