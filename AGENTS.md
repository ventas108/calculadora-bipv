# AGENTS.md

## Scope

This repository is a BIPV Colombia platform for shading calculation and simulation. This file applies globally to the repository and defines the working rules for any coding agent, including VS Code agents and Claude Code assistants.

## Core mission

Understand the current project state before changing anything. Identify the most probable objective from the existing code and documentation. Apply minimal, architecture-consistent improvements only when they are clearly necessary.

## Repository context

- Frontend: `client/`
- Backend: `server/`
- Shared contracts and logic: `shared/`
- Deployment documentation: `DEPLOY_README.md`
- Critical shading contract: `shared/shading-engine-contract.ts`
- Colombian region logic: `shared/colombianRegions.ts`
- Stack: React 19, Vite, Tailwind 4, Express, tRPC, TypeScript, pnpm

## Global operating rules

1. Review the repo state before changing anything.
2. Check branch state and git status before a significant task.
3. Read the relevant code in the involved modules before editing.
4. Preserve the existing architecture and contracts.
5. Do not ignore modules implicated in the calculation pipeline.
6. If the issue touches shading, irradiance, geometry, region classification, or energy calculation, validate shared and server logic before modifying UI behavior.
7. Keep changes minimal, compatible, and reversible.
8. Prefer compatibility with current behavior over speculative refactors.
9. Do not introduce unnecessary dependencies.
10. Validate with the smallest relevant command: typecheck, tests, or build if applicable.
11. Summarize at the end what was checked, what changed, and why.

## Required workflow for changes

### 1. Inspect the real execution path

Before implementing or proposing any fix, inspect the modules involved in the relevant process, including:

- `shared/` for contracts, region logic, and cross-layer data models
- `server/` for backend calculation and orchestration logic
- `client/` for UI integration only after shared and server behavior is understood
- `DEPLOY_README.md` for operating constraints and deploy expectations

### 2. Respect contract boundaries

The shading engine contract and region metadata are not optional implementation details. They are architectural guards.

- Do not break the shading contract.
- Do not mutate regional logic without checking downstream effects.
- Do not bypass validation logic already present in the codebase.

### 3. Keep the change minimal

Whenever possible:

- apply a narrow patch
- keep API shapes stable
- preserve established naming and data flow
- avoid broad refactors unrelated to the task

### 4. Use SDD + OpenSpec discipline

For non-trivial work, define the proposal before implementation.

Standard flow:

```text
/opsx:propose
/opsx:apply
/opsx:validate
/opsx:archive
```

The proposal should include:
- objective
- current state
- affected modules
- constraints
- expected behavior
- validation path
- compatibility and risk notes

Suggested structure:

```text
.openspec/
  proposals/
    <feature-or-fix>/
      proposal.md
      design.md
      tasks.md
      spec.yaml
```

### 5. Branch handling

- Create or switch to a task-specific branch when requested.
- Confirm repo status before creating a branch.
- Keep branch names descriptive and scoped to the work.

## Calculation-specific guidance

This project has calculation logic that spans more than one layer. Do not treat the frontend as the source of truth for business calculation semantics.

When the task impacts:
- shading
- irradiance
- geometry
- battery or production calculations
- Colombian region assumptions
- simulator outputs

then validate all of the following before finalizing the patch:

- shared contract and data structure definitions
- server-side calculation and validation logic
- client-side presentation or request mapping

## Traducción y contenido en español

Este repositorio tiene una fuerte orientación técnica y documental en español. Cuando el trabajo implique traducir, redactar o revisar textos del proyecto:

- Prioriza el español natural de Colombia, manteniendo precisión técnica y terminología del sector BIPV.
- No traduzcas nombres de archivos, rutas, módulos, variables, comandos, endpoints, claves JSON, SQL, schemas, acrónimos técnicos o identificadores de código.
- Conserva términos regulatorios, comerciales y de ingeniería si forman parte del lenguaje del producto o del dominio de negocio.
- Mantén el significado original, la estructura del documento y la intención del autor; evita traducciones literales que rompan claridad técnica.
- Si una frase es ambigua, preserva la terminología técnica correcta y usa un español claro y neutral.
- Para textos de usuario o documentación, prioriza claridad antes que literalidad; para contenido técnico, prioriza precisión antes que estilo.

## Validation requirements

After a meaningful change, run the smallest relevant verification command:

- TypeScript check if types changed
- focused tests if a relevant suite exists
- build if compilation is impacted
- targeted project validation if no narrow command exists

If there is uncertainty, prefer honest partial validation over unsupported claims.

## Final summary expectation

At the end of the work, report:

1. what was reviewed
2. what modules were involved
3. what changed
4. why the change was necessary
5. what validation was run and the outcome
6. what risks remain, if any

## Intent for Claude Code

Claude Code should act as the implementation bridge, not as an ungrounded refactor engine. The agent must stay aligned with the project’s actual architecture and calculation contracts.

The correct pattern is:

- VS agent / repo instructions define the plan and constraints
- Claude Code executes the implementation within those boundaries
- OpenSpec keeps the proposal and validation explicit and traceable
