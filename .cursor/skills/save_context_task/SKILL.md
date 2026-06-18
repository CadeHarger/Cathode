---
name: save_context_task
description: Instructions for creating a subtask in a way that saves context in Cathode
---

## When to Use

- Use this skill only when invoked by the user

## Instructions

- When invoked, the user wants you to complete the task using subagent(s) (Composer 2.5 unless otherwise specified) to save context in the main thread.
- All code exploration should be done by the subagent. Provide the problem description and relevant context from your thread.
- Point subagents at `/generic_context` or the relevant schema file (`backend/backend_schema.yaml`, `cathode-frontend/frontend_schema.yaml`) so they orient quickly without re-reading the whole repo.
- Example: after implementing a feature, delegate writing tests to a subagent — narrow scope, but setup exploration would bloat the main thread.
