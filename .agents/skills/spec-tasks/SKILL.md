---
name: spec-tasks
description: Generate step-by-step tasks and the UML for the current spec's planned development in this project.
---

# Spec Tasks

Step-by-step implementation of a technical plan.

## Language of the spec

Written entirely in `tasks.md` format in **Spanish**: section titles, placeholders
filled in, user stories, EARS requirements and notes.

## Process

1. You must receive the name or reference to a `spec.md` and a `plan.md`. Wait for these two inputs; do nothing else until you receive them.
2. Once obtained, generate `tasks.md` next to them, with small tasks (max. 20-30 min each), in dependency order, each one
with the RFs it covers and a verifiable "Done when:" line. Use checkboxes.
3. In the same run, create or overwrite `uml.md` next to `spec.md`, `plan.md` and `tasks.md` in **this project's** spec folder. The UML documents the development described by that plan/tasks for this repository.

## UML (`uml.md`)

- Prose in Spanish; Mermaid identifiers may keep real planned code names (classes, files, routes, env vars).
- Prefer one sequence diagram of the main flow plus one structure diagram (`classDiagram`, `flowchart`, or component layout) aligned with the plan and this project's conventions (`AGENTS.md` / architecture skills).
- Cite concrete paths, endpoints, cookies, env vars and JSON shapes as defined for this cut.
- Do not invent types or layers outside the plan or this project's architecture.
- If `uml.md` already exists, replace it so it matches this plan/tasks run.

## UML Relationship Hygiene

Class diagrams should communicate architecture, not reproduce every import or local variable type.

Prefer architecturally meaningful relationships over exhaustive compile-time dependency graphs.

Avoid duplicating transitive relationships when a clearer owner relationship already explains the dependency.

Example: if `GoogleLoginService` depends on `GoogleOAuthClient`, and `GoogleOAuthClient` returns or maps `GoogleProfile`, show `GoogleLoginService --> GoogleOAuthClient` and `GoogleOAuthClient ..> GoogleProfile`; omit `GoogleLoginService ..> GoogleProfile` unless the service owns important rules around that profile type.

For UML diagrams:

- show fields, constructor collaborators, interfaces, adapters, repositories, clients, and framework-facing boundaries
- show DTOs or records when they are public contracts or key outputs
- omit transient local-variable types when their relationship is already explained by a repository, client, adapter, or returned contract
- omit duplicated edges from a service to entities when the repository relationship already communicates ownership/access clearly
- keep the diagram readable even if that means it is not a complete import graph
