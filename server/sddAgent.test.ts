import { describe, expect, it } from "vitest";
import path from "node:path";
import {
  auditSpec,
  DIRECTOR_DOCUMENTS,
  readDirectorContext,
  resolveDirectorDirectory,
} from "./sddAgent";

describe("SDD agent gate", () => {
  it("loads the mandatory hybrid-app policy into director context", () => {
    expect(DIRECTOR_DOCUMENTS).toContain("separacion-apps.md");
  });

  it("resolves the same director for top-level and nested specs", () => {
    const expected = path.resolve("CodeSpecs/00-director");
    expect(resolveDirectorDirectory("CodeSpecs/01-datos-proyecto")).toBe(expected);
    expect(resolveDirectorDirectory("CodeSpecs/02-recurso-solar/react")).toBe(expected);
    expect(resolveDirectorDirectory(path.resolve("CodeSpecs/02-recurso-solar/react"))).toBe(expected);
  });

  it("includes the hybrid-app policy content for a nested spec", async () => {
    const context = await readDirectorContext("CodeSpecs/02-recurso-solar/react");
    expect(context).toHaveLength(DIRECTOR_DOCUMENTS.length);
    expect(context.map(section => section.match(/^## Director: (.+)$/m)?.[1])).toEqual([
      ...DIRECTOR_DOCUMENTS,
    ]);
    const hybridPolicy = context.find(section =>
      section.startsWith("## Director: separacion-apps.md"),
    );
    expect(hybridPolicy).toContain("# Separación de apps");
  });

  it("blocks incomplete specs before any model review", async () => {
    const audit = await auditSpec("CodeSpecs/02-recurso-solar/streamlit");

    expect(audit.canRequestReview).toBe(false);
    expect(audit.canRunPreparation).toBe(false);
    expect(audit.canAdvanceToImplementation).toBe(false);
    expect(audit.state).toBe("idea");
    expect(audit.missingDocuments).toEqual([]);
    expect(audit.incompleteDocuments).toContain("problema.md");
    expect(audit.incompleteDocuments).toContain("propuesta.md");
    expect(audit.advanceBlockingReasons).toEqual(
      expect.arrayContaining([expect.stringContaining("aprobación humana")]),
    );
    expect(audit.blockingReasons).toEqual(
      expect.arrayContaining([expect.stringContaining("Documentos incompletos")]),
    );
  });
});