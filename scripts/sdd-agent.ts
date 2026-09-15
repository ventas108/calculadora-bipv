import "dotenv/config";
import { auditSpec, readSpecForReview } from "../server/sddAgent.ts";

const model = process.env.ANTHROPIC_MODEL ?? "claude-sonnet-5";

function getSpecPath(): string {
  const index = process.argv.indexOf("--spec");
  const specPath = index >= 0 ? process.argv[index + 1] : undefined;
  if (!specPath) {
    throw new Error("Uso: pnpm exec tsx scripts/sdd-agent.ts --spec CodeSpecs/01-datos-proyecto");
  }
  return specPath;
}

function hasFlag(flag: string): boolean {
  return process.argv.includes(flag);
}

function printEarlyAlerts(audit: Awaited<ReturnType<typeof auditSpec>>): void {
  for (const reason of audit.blockingReasons) {
    console.error(`SDD ALERTA [BLOQUEO] ${reason}`);
  }
  for (const reason of audit.advanceBlockingReasons) {
    if (!audit.blockingReasons.includes(reason)) {
      console.error(`SDD ALERTA [AVANCE] ${reason}`);
    }
  }
  for (const risk of audit.integrationRisks) {
    console.warn(`SDD ALERTA [RIESGO] ${risk}`);
  }
}

async function requestReview(specPath: string): Promise<unknown> {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    throw new Error("ANTHROPIC_API_KEY es obligatorio para solicitar revisión");
  }

  const spec = await readSpecForReview(specPath);
  const response = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "content-type": "application/json",
      "x-api-key": apiKey,
      "anthropic-version": "2023-06-01",
    },
    body: JSON.stringify({
      model,
      max_tokens: 2000,
      system:
        "Eres un agente de preparación y control SDD en una arquitectura híbrida. Devuelve JSON con: hallazgos, entradas_salidas_contratos, dependencias, archivos_probablemente_afectados, riesgos_integracion, tareas_propuestas y validaciones_faltantes. No ejecutes comandos, no modifiques código, no cambies contratos, no tomes decisiones arquitectónicas, no apruebes la Spec y detén el flujo si faltan datos o hay incompatibilidades. La aprobación humana y las validaciones reales siguen siendo obligatorias.",
      messages: [{ role: "user", content: spec }],
    }),
  });

  if (!response.ok) {
    throw new Error(`Anthropic respondió HTTP ${response.status}: ${await response.text()}`);
  }
  return response.json();
}

async function main(): Promise<void> {
  const specPath = getSpecPath();
  const audit = await auditSpec(specPath);
  console.log(JSON.stringify(audit, null, 2));
  printEarlyAlerts(audit);

  if (hasFlag("--fail-on-block") && !audit.canRequestReview) {
    process.exitCode = 2;
  }
  if (hasFlag("--fail-on-preparation-block") && !audit.canRunPreparation) {
    process.exitCode = 2;
  }

  if (!audit.canRunPreparation || !hasFlag("--review")) {
    return;
  }
  console.log(JSON.stringify(await requestReview(specPath), null, 2));
}

main().catch(error => {
  console.error(error instanceof Error ? error.message : error);
  process.exitCode = 1;
});