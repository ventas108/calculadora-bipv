import {
  isOfficialShadingEngineResult,
  SHADING_ENGINE_CONTRACT_VERSION,
  type ShadingEngineRequest,
  type ShadingEngineResult,
} from "@shared/shading-engine-contract";

export async function runOfficialShadingEngine(
  request: ShadingEngineRequest,
): Promise<ShadingEngineResult> {
  const response = await fetch("/api/shading-engine/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  const payload: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    const message =
      payload && typeof payload === "object" && "error" in payload
        ? String((payload as { error: unknown }).error)
        : `Error HTTP ${response.status}`;
    throw new Error(message);
  }
  if (!isOfficialShadingEngineResult(payload)) {
    throw new Error(
      `Respuesta incompatible con el contrato ${SHADING_ENGINE_CONTRACT_VERSION}`,
    );
  }
  return payload;
}