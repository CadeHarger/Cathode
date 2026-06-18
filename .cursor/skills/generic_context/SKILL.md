---
name: generic_context
description: Contains generic context for how to locate documentation for the Cathode project, as well as other general implementation rules
---

## When to Use

- Use this skill only when invoked by the user, or when providing context to subagents and you deem this to be necessary, or when referenced in another skill you're using

## Instructions

Cathode is a music playlist recommendation app: users describe a life experience, the backend generates cathartic song picks via a hybrid pipeline (Gemini → Spotify → vector search over ~5M lyrics → LLM re-rank), and the React frontend polls async jobs for results.

- Before reading other files, read the schema files for structural orientation:
  - `backend/backend_schema.yaml` — Python backend: FastAPI job API, hybrid search pipeline, DataManager/FAISS
  - `cathode-frontend/frontend_schema.yaml` — React frontend: Vite SPA, 3-step wizard, job polling
- Archived code lives in `archive/` (abandoned GCP deployment, legacy playlistAgent) — not active.
- Read whichever schema is relevant to the task (both if the change spans API contract or full-stack flow).
- If any part of the implementation is unclear, use the ask questions tool if you need to clarify requirements with the user.
- Update these schema files when significant enough changes are made to be mentioned there. Keep them concise — roughly 2 sentences per entry is enough for most files; more for complex modules.
- When finished with backend functionality changes, add or update tests if a test suite exists for the area you changed.
