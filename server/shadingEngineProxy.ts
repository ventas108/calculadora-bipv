import type { Express, Request, Response } from "express";
import { spawn } from "node:child_process";
import path from "node:path";

const PROJECT_ROOT = path.resolve(process.cwd());
const PYTHON = process.env.BIPV_PYTHON || "python";
const SCRIPT = path.join(PROJECT_ROOT, "bipv_python", "scripts", "run_shading_contract.py");

export function registerShadingEngineProxy(app: Express) {
  app.post("/api/shading-engine/run", (req: Request, res: Response) => {
    const child = spawn(PYTHON, [SCRIPT], {
      cwd: PROJECT_ROOT,
      env: { ...process.env, PYTHONPATH: path.join(PROJECT_ROOT, "bipv_python") },
      stdio: ["pipe", "pipe", "pipe"],
    });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (chunk: Buffer) => { stdout += chunk.toString(); });
    child.stderr.on("data", (chunk: Buffer) => { stderr += chunk.toString(); });
    child.on("error", (error) => {
      res.status(502).json({ error: `No se pudo iniciar el motor Python: ${error.message}` });
    });
    child.on("close", (code) => {
      if (res.headersSent) return;
      if (code !== 0) {
        let details: unknown = stderr.trim() || stdout.trim() || "Error desconocido";
        try { details = JSON.parse(stdout); } catch { /* texto de proceso */ }
        res.status(422).json({ error: "El motor solar rechazó la solicitud", details });
        return;
      }
      try {
        res.json(JSON.parse(stdout));
      } catch {
        res.status(502).json({ error: "El motor solar devolvió una respuesta inválida" });
      }
    });
    // express.json() ya consumió el stream HTTP; reenviar el cuerpo parseado
    // explícitamente al proceso Python evita que reciba stdin vacío.
    child.stdin.end(JSON.stringify(req.body ?? {}));
  });
  console.log("[Shading Engine] Python official engine registered at /api/shading-engine/run");
}