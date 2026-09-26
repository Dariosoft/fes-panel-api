---
name: resolve-tasks
description: Resolve the open questions left for the current spec.
---

## Process

- Open the `tasks.md` mentioned in the conversation.
- Complete each T one by one, run the unit tests between each T, and mark it in `tasks.md` at the end of each T implementation.
- If a test fails, go back over the last T to debug and try to fix what broke in that test. You may retry up to 2 times.
- If it is still not fixed, do not keep resolving any further T. Instead, create a file next to `tasks.md` with the problem's stack trace.
- If a T requires manual validation, ignore it. You must not resolve that kind of task.

## Limitation

This skill modifies local code. It does not push any changes to the repositories.
