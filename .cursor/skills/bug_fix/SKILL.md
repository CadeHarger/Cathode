---
name: bug_fix
description: Instructions for efficiently using context when fixing bugs in Cathode. Only manually used
---

## When to Use

- Use this skill only when invoked by the user

## Instructions

Your goal is to fix the bug(s) the user has provided, doing so with minimal token usage.

Before reading other files, orient yourself with the Cathode schema files:
- `backend/backend_schema.yaml` — when the bug lives in `backend/`
- `cathode-frontend/frontend_schema.yaml` — when the bug lives in `cathode-frontend/`

Read the schema for the layer where the bug lives; read both if the issue spans the API contract or full-stack flow.

When finished:
- Frontend-only fix: add a test only if a frontend test suite exists
- Backend fix: add or update tests under `backend/tests/` if that directory exists; Cathode currently has no formal test suite — propose tests to the user if the fix warrants regression coverage
