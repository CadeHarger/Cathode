---
name: test_coverage_audit
description: Instructions for auditing test coverage in Cathode and planning new tests to remediate gaps
---

## When to Use

- Use this skill only when invoked by the user

## Instructions

Your goal is to identify gaps in Cathode's testing and propose a plan to close them.

Use the `/generic_context` skill for project orientation. Cathode currently has **no formal test suite** — this skill is for establishing or expanding coverage.

## What to cover

Read `backend/backend_schema.yaml` and `cathode-frontend/frontend_schema.yaml` to understand scope, then map functionality to tests:

**Backend (`backend/`):**
- Hybrid search pipeline: query generation, Spotify intersection, vector search, LLM re-rank
- `DataManager` / FAISS search and song lookup
- FastAPI job lifecycle: create, poll, cancel
- `llm_filter` lyrics loading and scoring (mock external APIs)
- Prefer unit tests with mocked Spotify/Gemini; never call real LLM or Spotify APIs in CI

**Frontend (`cathode-frontend/`):**
- 3-step wizard state transitions
- `useJobPolling` / `useCreatePlaylist` behavior (mock `fetch`)
- Results rendering and title editing
- UI tests are lower priority than API/pipeline tests unless the user asks for them

## Constraints

- Tests must not make real API calls to LLMs, Spotify, or Vertex AI (cost and flakiness).
- Gitignored `backend/data/` and `backend/models/` are not available in CI — mock or use tiny fixtures.

## Workflow

Use subagents to scan each layer against existing tests (if any) and report gaps. Refine their findings, then produce a phased plan: what to test first, suggested file layout (`backend/tests/`, Vitest/Playwright if added), and mocking strategy.

Watch for non-traditional gaps:
- Hardcoded `localhost:8000` in frontend hooks
- Local vs cloud `data_manager` divergence
- Schema/API contract drift between `backend_schema.yaml` and `frontend_schema.yaml`
