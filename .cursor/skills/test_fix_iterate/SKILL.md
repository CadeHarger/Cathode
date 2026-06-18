---
name: test_fix_iterate
description: Instructions for running tests, fixing failures, and iterating in Cathode. Only run when manually called.
---

## When to Use

- Use this skill when manually called.

## Instructions

- When looking for where to make changes, read `backend/backend_schema.yaml` and/or `cathode-frontend/frontend_schema.yaml` before exploring on your own.

**If working on the backend (`backend/`):**
- Read `backend/backend_schema.yaml`.
- Run tests via `cd backend && python -m pytest tests/ -q` if `backend/tests/` exists.
- Plan where to make changes. If implementation intent is unclear, use the ask questions tool.
- Implement changes.
- Summarize context to save tokens, keeping only what matters for the next iteration.
- Repeat until all tests pass or the same bug fails twice (then escalate to the user).

**If working on the frontend (`cathode-frontend/`):**
- Read `cathode-frontend/frontend_schema.yaml`.
- Run `npm run lint` from `cathode-frontend/`.
- Run `npm run build` to catch compile errors.
- If a test script exists in `package.json`, run it; Cathode currently has no frontend test suite.
- Implement changes and repeat until checks pass or the same issue fails twice.

**If working full-stack (API + UI):**
- Read both `backend/backend_schema.yaml` and `cathode-frontend/frontend_schema.yaml`.
- Verify API contract sections in both schemas still match (request/response shapes, job polling, song fields).
- Run backend and frontend checks as above.

Notes:
- Cathode has no Playwright E2E or integration-agent test harness yet.
- Overlapping coverage between unit and integration tests is fine when both exist; don't over-test constants or trivial wiring.

Principles:
- Non-integration tests should be (mostly) mutually exclusive and (mostly) collectively exhaustive.
