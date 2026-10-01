---
name: resolve-concerns
description: Resolve the open questions left for the current spec.
---

## Process

- Leave a message in the conversation with a link to quickly open the spec window, so I can read it while answering questions.
- Meanwhile, ask me the questions that are still pending. Always give me the option to stop answering them. I should be able to continue later if I want.
- When I finish answering the questions, or when I interrupt the questionnaire with that option, update the spec.
- Strike through each question that has been answered.
- When every question has been answered satisfactorily, delete the `concerns.md` file.
- Then, start a subagent in charge of running the `spec-generator` skill of the same project, using the final spec produced while resolving the concerns.
- When that skill finishes running, start the `spec-tasks` skill with the generated `spec.md` and the `plan.md` produced in that same subagent thread.
- The final result must create `tasks.md` and `uml.md`.

## Limitation

This skill only modifies all documentation into spec/ folder (`spec.md`, `concerns.md`, `plan.md`, `tasks.md`, `uml.md`) files. It does not edit any other part of the code.
It must always use the context belonging to the project it is in, and must not modify any other project.
