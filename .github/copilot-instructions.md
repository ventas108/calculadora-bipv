# Copilot Instructions for calculadora-bipv

## Global repository rules

This repository is a BIPV Colombia project for shading, irradiance, and simulation. Work conservatively and keep the existing architecture intact.

## Mission

Understand the current state of the project before making a change. Identify the most probable objective from the code and documentation. Apply only necessary improvements that are consistent with the architecture and contracts already in place.

## Mandatory constraints

- Preserve the established frontend/backend/shared boundaries.
- Respect the shading engine contract in `shared/shading-engine-contract.ts`.
- Respect Colombian region logic in `shared/colombianRegions.ts`.
- Do not ignore modules involved in the calculation path.
- Do not treat UI-only changes as the root cause for a calculation bug.
- Do not add dependencies unless there is a strong and documented need.
- Do not break validation rules or downstream compatibility.

## Required workflow before editing

1. Inspect the repo status and current branch.
2. Read the relevant shared, server, and client files.
3. Identify the real calculation path and the modules it crosses.
4. If the issue is related to shading, irradiance, regions, or production calculations, validate shared and server logic before changing the frontend.
5. Keep the patch minimal and architecture-aligned.

## SDD / OpenSpec workflow

For meaningful work, use an explicit specification-first flow:

```text
/opsx:propose
/opsx:apply
/opsx:validate
/opsx:archive
```

Use a proposal structure like:

```text
.openspec/
  proposals/
    <feature-or-fix>/
      proposal.md
      design.md
      tasks.md
      spec.yaml
```

The proposal should describe:
- objective
- current state
- affected modules
- constraints
- validation path
- compatibility risks

## Repository-specific context

- Stack: React 19, Vite, Tailwind 4, Express, tRPC, TypeScript, pnpm.
- Frontend lives in `client/`.
- Backend logic lives in `server/`.
- Shared contracts and calculation logic live in `shared/`.
- Deployment references are in `DEPLOY_README.md`.

## Calculation integrity

Do not ignore details in the modules involved in each calculation process. For example:

- shading calculation modules
- irradiance inputs and transformations
- region classification
- server-side calculation orchestration
- UI mapping and display logic

The correct ordering is:

1. understand shared contract and server logic
2. verify the calculation model
3. apply a minimal fix
4. validate before adjusting presentation

## Traducción y contenido en español

Este repositorio usa el español como lenguaje predominante para documentación y comunicación técnica. Si la tarea exige traducir o revisar textos:

- Mantén el español claro y técnico, con terminología apropiada para BIPV, energía solar y simulación.
- No traduzcas nombres de código, rutas, comandos, variables, endpoints, columnas de base de datos, keys JSON ni identificadores.
- Conserva referencias regulatorias, acrónimos y marcas de software tal como aparecen en contexto técnico.
- Prioriza la precisión del contenido sobre la literalidad; la traducción debe reflejar el mismo significado sin perder detalle técnico.
- En caso de duda, usa la terminología establecida en la documentación del proyecto y evita inventar nombres nuevos.

## Validation

After a change, run the smallest relevant validation command:

- TypeScript check if types changed
- targeted tests if they exist
- build if compilation is affected
- project validation if no narrower command exists

Do not claim success without verification evidence.

## Final response format

At the end, summarize:

- what was reviewed
- what modules were involved
- what changed
- why it was necessary
- which validation checks were run
- any remaining risks or follow-up items

## Purpose

This instruction set is intended to keep the repository coherent, compatible, and calculation-safe while enabling a disciplined OpenSpec plus Claude Code implementation flow.
