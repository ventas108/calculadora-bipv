import { describe, expect, it } from "vitest";
import { auditSpec } from "./sddAgent";

describe("SDD agent gate", () => {
  it("blocks incomplete specs before any model review", async () => {
    const audit = await auditSpec("CodeSpecs/01-datos-proyecto");

    expect(audit.canRequestReview).toBe(false);
    expect(audit.canAdvanceToImplementation).toBe(false);
    expect(audit.state).toBe("idea");
    expect(audit.missingDocuments).toContain("propuesta.md");
    expect(audit.incompleteDocuments).toContain("problema.md");
    expect(audit.advanceBlockingReasons).toEqual(
      expect.arrayContaining([expect.stringContaining("aprobación humana")]),
    );
    expect(audit.blockingReasons).toEqual(
      expect.arrayContaining([
        expect.stringContaining("Faltan documentos"),
        expect.stringContaining("Documentos incompletos"),
      ]),
    );
  });
});