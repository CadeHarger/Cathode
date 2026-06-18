---
name: file_too_big
description: Instructions for refactoring files that are too big in Cathode.
---

## When to Use

- Use this skill only when invoked by the user

## Instructions

- The referenced file is too big. Spread existing functionality across existing or new files where fit. You can keep the existing file, but keep LOC under 1000. Files over 1000 LOC beyond the one specified are out of scope until asked.
- For understanding what other files exist, read `backend/backend_schema.yaml` and/or `cathode-frontend/frontend_schema.yaml` depending on which layer you're in.
- Update imports affected by the refactor. Update the relevant schema file when done.
- Tell the user the net line count change across all touched files.
