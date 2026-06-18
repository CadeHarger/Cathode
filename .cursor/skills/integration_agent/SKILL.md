---
name: integration_agent
description: Not applicable to Cathode — legacy skill from another project. Use manual or scripted testing against the local API and frontend instead.
---

## When to Use

- Do not use this skill in the Cathode repo unless the user explicitly asks to port or add an integration-agent harness.

## Instructions

Cathode does not include an `integration_agent/` service or Playwright E2E suite.

For exploratory or end-to-end testing in this project:
- Read `backend/backend_schema.yaml` and `cathode-frontend/frontend_schema.yaml` for architecture and API contract.
- Run the backend: `python backend/start_server.py` (requires `.env` with Spotify and Gemini keys).
- Run the frontend: `npm run dev` in `cathode-frontend/`.
- Exercise the 3-step playlist flow manually or with a small script that POSTs `/api/playlist` and polls `/api/job/{job_id}`.

If the user wants automated browser testing, propose adding Playwright under `cathode-frontend/` or a dedicated `e2e/` folder and document it in `frontend_schema.yaml`.
