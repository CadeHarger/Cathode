---
name: documentation_grounding
description: Instructions for revising grounding of Cathode project documentation maps, ensuring efficient token usage and accuracy.
---

## When to Use

- Use this skill only when invoked by the user

## Instructions

Cathode uses YAML schema files at the repo root to give agents quick project context without reading every source file.

Your goal is to make sure the documentation file specified by the user when invoking this skill is up-to-date, accurate, and not excessive in length/token usage.

## Development-level documents

Guidelines:
- The file purpose and project description should be at the top.
- Every non-trivial file/folder should have a 2–3 sentence description of its purpose. Trivial paths (venv, node_modules, gitignored data/models) can be omitted or noted briefly.
- Stick to high-level engineering concepts — avoid listing every function or variable name.

Cathode docs:
- `./backend/backend_schema.yaml` — Overview of `backend/`: API server, hybrid search pipeline, data layer, data-prep scripts. Read when modifying backend code or API contracts.
- `./cathode-frontend/frontend_schema.yaml` — Overview of `cathode-frontend/`: pages, components, hooks, routing, API integration. Read when modifying the React app.
- `./archive/README.md` — Archived cloud deployment and legacy code (not maintained).

Both schemas include conceptual sections (pipeline, API contract, creation flow, known gaps) that agents should keep accurate when behavior changes.
