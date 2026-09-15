import { promises as fs } from "node:fs";
import path from "node:path";

export const SPEC_DOCUMENTS = [
  "problema.md",
  "propuesta.md",
  "diseno.md",
  "tareas.md",
  "implementacion.md",
  "validacion.md",
] as const;

export type SpecDocument = (typeof SPEC_DOCUMENTS)[number];
export type SpecState =
  | "idea"
  | "propuesta"
  | "diseño"
  | "aprobado"
  | "en implementación"
  | "validación"
  | "completado"
  | "archivado";

export type SpecAudit = {
  specPath: string;
  state: SpecState | null;
  missingDocuments: SpecDocument[];
  incompleteDocuments: SpecDocument[];
  missingRequirements: string[];
  affectedLayers: string[];
  affectedFiles: string[];
  integrationRisks: string[];
  validationCommands: string[];
  blockingReasons: string[];
  canRequestReview: boolean;
  canRunPreparation: boolean;
  advanceBlockingReasons: string[];
  canAdvanceToImplementation: boolean;
};

const REQUIRED_SECTIONS: Record<SpecDocument, string[]> = {
  "problema.md": ["Problema a resolver", "Contexto"],
  "propuesta.md": ["Objetivo", "Alternativa recomendada"],
  "diseno.md": [
    "Entradas",
    "Salidas",
    "Tipos de datos",
    "Errores posibles",
    "Dependencias",
    "Criterios de aceptación",
  ],
  "tareas.md": [],
  "implementacion.md": ["Cambios realizados", "Archivos modificados"],
  "validacion.md": ["Checklist de validación del módulo", "Resultado"],
};

const LAYERS = ["cálculo", "API", "estado", "interfaz"];

function matchAllGroups(content: string, pattern: RegExp): string[] {
  const results: string[] = [];
  let match: RegExpExecArray | null;
  while ((match = pattern.exec(content)) !== null) {
    results.push(match[1]);
    if (match.index === pattern.lastIndex) {
      pattern.lastIndex += 1;
    }
  }
  return results;
}

function hasSection(content: string, section: string): boolean {
  const escaped = section.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return new RegExp(`^##\\s+${escaped}\\s*$`, "im").test(content);
}

function nonEmptySection(content: string, section: string): boolean {
  const escaped = section.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const match = content.match(new RegExp(`^##\\s+${escaped}\\s*$([\\s\\S]*?)(?=^##\\s|$)`, "im"));
  return Boolean(match && !/\bpendiente\b|\(_\)|^\s*-\s*$|^\s*-\s*\[ \]\s*$/im.test(match[1]));
}

function readState(content: string): SpecState | null {
  const match = content.match(/^\*\*Estado:\*\*\s*(.+?)\s*$/im);
  const state = match?.[1].toLowerCase() as SpecState | undefined;
  return state && [
    "idea",
    "propuesta",
    "diseño",
    "aprobado",
    "en implementación",
    "validación",
    "completado",
    "archivado",
  ].includes(state)
    ? state
    : null;
}

export async function auditSpec(specPath: string): Promise<SpecAudit> {
  const missingDocuments: SpecDocument[] = [];
  const incompleteDocuments: SpecDocument[] = [];
  const missingRequirements: string[] = [];
  const contents = new Map<SpecDocument, string>();

  for (const document of SPEC_DOCUMENTS) {
    try {
      const content = await fs.readFile(path.join(specPath, document), "utf8");
      contents.set(document, content);
      if (/\bpendiente\b|\(_\)|^-\s*$|^-\s*\[ \]\s*$/im.test(content)) {
        incompleteDocuments.push(document);
      }
      for (const section of REQUIRED_SECTIONS[document]) {
        if (!hasSection(content, section) || !nonEmptySection(content, section)) {
          missingRequirements.push(`${document}: sección incompleta «${section}»`);
        }
      }
    } catch {
      missingDocuments.push(document);
    }
  }

  const state = contents.has("problema.md")
    ? readState(contents.get("problema.md")!)
    : null;
  const blockingReasons: string[] = [];

  if (missingDocuments.length > 0) {
    blockingReasons.push(`Faltan documentos: ${missingDocuments.join(", ")}`);
  }
  if (incompleteDocuments.length > 0) {
    blockingReasons.push(
      `Documentos incompletos: ${incompleteDocuments.join(", ")}`,
    );
  }
  if (missingRequirements.length > 0) {
    blockingReasons.push(`Requisitos incompletos: ${missingRequirements.join("; ")}`);
  }
  const canRequestReview = blockingReasons.length === 0;
  const canRunPreparation = canRequestReview && state === "aprobado";
  const advanceBlockingReasons = [...blockingReasons];
  if (state !== "aprobado") {
    advanceBlockingReasons.push(
      state
        ? `La Spec requiere aprobación humana; estado actual: ${state}`
        : "No se pudo determinar un estado válido en problema.md",
    );
  }
  const canAdvanceToImplementation = advanceBlockingReasons.length === 0;
  const design = contents.get("diseno.md") ?? "";
  const validation = contents.get("validacion.md") ?? "";
  const implementation = contents.get("implementacion.md") ?? "";
  const affectedLayers = LAYERS.filter(layer => new RegExp(`\\b${layer}\\b`, "i").test(
    `${design}\n${implementation}`,
  ));
  const affectedFiles = matchAllGroups(
    implementation,
    /`([^`]+\.(?:ts|tsx|py|md|json|sql|env))`/g,
  );
  const integrationRisks: string[] = [];
  if (/m[oó]dulos dependientes|m[oó]dulos previos/i.test(design)) {
    integrationRisks.push("La Spec tiene dependencias entre módulos; comprobar contratos antes de implementar.");
  }
  if (affectedLayers.length > 1) {
    integrationRisks.push("La Spec atraviesa varias capas; requiere validación de integración.");
  }
  if (specPath.includes("09-despliegue")) {
    integrationRisks.push("Despliegue: revisar migraciones, variables de entorno, artefactos y rollback.");
  }
  const validationCommands = matchAllGroups(validation, /`([^`]+)`/g);

  return {
    specPath,
    state,
    missingDocuments,
    incompleteDocuments,
    missingRequirements,
    affectedLayers,
    affectedFiles,
    integrationRisks,
    validationCommands,
    blockingReasons,
    canRequestReview,
    canRunPreparation,
    advanceBlockingReasons,
    canAdvanceToImplementation,
  };
}

export async function readSpecForReview(specPath: string): Promise<string> {
  const audit = await auditSpec(specPath);
  if (!audit.canRunPreparation) {
    throw new Error(`Spec bloqueada: ${audit.advanceBlockingReasons.join("; ")}`);
  }

  const directorFiles = [
    "vision.md",
    "arquitectura-global.md",
    "contratos-entre-modulos.md",
    "mapa-dependencias.md",
    "registro-de-decisiones.md",
  ];
  const directorContext = await Promise.all(
    directorFiles.map(async document => {
      const content = await fs.readFile(path.join(specPath, "..", "00-director", document), "utf8");
      return `## Director: ${document}\n\n${content}`;
    }),
  );
  const sections = await Promise.all(
    SPEC_DOCUMENTS.map(async document => {
      const content = await fs.readFile(path.join(specPath, document), "utf8");
      return `## ${document}\n\n${content}`;
    }),
  );
  return [...directorContext, ...sections].join("\n\n");
}