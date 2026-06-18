---
name: agent_dev_loop
description: Instructions for effectively improving AI-driven flows within Cathode (e.g. hybrid search, LLM prompts)
---

## When to Use

- Use this skill only when invoked by the user

## Instructions

STEP 1: Run the user's specified agent flow against the specified benchmark (e.g. `hybrid_agent.py` CLI, API job with a fixed prompt, or a batch of test experiences).

STEP 2: Inspect errors and delegate objectively broken code to subagents. Do not change prompts in this step — only fix uncaught code errors. If agent output causes errors, reason about expected failure handling in the pipeline and proceed.

STEP 3: Inspect the agent report vs output and the initial goal. Plan minimal prompt or pipeline changes. Read `backend/backend_schema.yaml` (pipeline section) for architecture context.

STEP 4: Use the ask questions tool to confirm each proposed change with the user.

STEP 5: Implement approved changes. Repeat until the user stops you or benchmark results are satisfactory.
