---
name: spec-generator
description: Use this skill when the user asks to create, write, or review a feature specification (spec). It writes spec.md immediately from the available context, leaves open questions as [NECESITA ACLARACIÓN], and writes concerns.md beside it ordered by necessity only when at least one question remains. Generated specs are always written in Spanish.
---

# Spec generator

Turn a vague idea into a specification. The spec is the
contract: if something is not here, it is not implemented.
Open questions stay visible; they are not a reason to wait.

## Language of the spec

Write the entire `spec.md` in **Spanish**: section titles, placeholders
filled in, user stories, EARS requirements, notes, and
`[NECESITA ACLARACIÓN]` markers. Do not mix English into the spec body.
Copy headings and EARS patterns from `spec-template.md` as-is.
Write `concerns.md` in Spanish as well.

## Process

1. **Read the context.** `docs/constitution.md` if it exists, and previous specs
   in `specs/` so you respect conventions and do not contradict what was already agreed.
2. **Write now.** Do not interview and do not wait for confirmation before
   creating the files. Use the issue, the conversation, and the docs you
   already have. Where an answer would change what gets built and you do not
   have it, leave the gap open. Do not invent it. Do not propose technical
   solutions: the spec stays on the WHAT.
3. **Choose the number.** You may receive an implementation number in 3-digit format.
   If not, look at `specs/` and use the next free number with three digits: `specs/NNN-<name-in-kebab-case>/spec.md`
   (Only the created folder must be in English).
4. **Write `spec.md`** using `spec-template.md` from this skill, without skipping
   sections. Keep every section title in Spanish as in the template.
   Acceptance criteria **always in EARS notation in Spanish**, numbered
   as RF-1, RF-2, … Each requirement must be verifiable: if you cannot think of
   how to check it, it is poorly written.
5. **Mark what you do not know** as `[NECESITA ACLARACIÓN: pregunta concreta]`
   in the spec, including the "Dudas abiertas" section.
   Never fill a gap by inventing: a visible gap is information,
   a silent assumption is debt.
6. **Write `concerns.md` only when there is at least one open doubt**, in the
   same folder as `spec.md`. If nothing is open, do not create the file.
   List every open doubt, one per item, ordered by necessity: the doubt
   whose answer most changes what must be built comes first. Each item
   repeats the `[NECESITA ACLARACIÓN: pregunta concreta]` text from the spec
   and says why that answer is needed.
7. Do not start the plan or write code from this skill.

## Rules

- The spec describes **WHAT** and **WHY**. Do not include stack, architecture,
  file names, data schemas, algorithms, or function signatures:
  that belongs in the plan.
- Always include the "Fuera de alcance" section. It is what keeps the
  feature from growing on its own.
- One requirement, one sentence. If you need an "y" to join two behaviors,
  they are two requirements.
- No unmeasurable adjectives: "rápido", "intuitivo", "robusto" are not
  requirements. Write the threshold or do not write it.

## EARS notation

Five patterns. Choose the matching one; do not mix them.
Write them in Spanish as below; do not use English keywords
(`WHEN`, `THE SYSTEM SHALL`, etc.) in the spec.

| Pattern | Form | When |
|---|---|---|
| Ubiquitous | EL SISTEMA \<hará\> | always true |
| Event-driven | CUANDO \<disparador\>, EL SISTEMA \<hará\> | responds to something |
| State | MIENTRAS \<estado\>, EL SISTEMA \<hará\> | during a condition |
| Optional | DONDE \<característica\>, EL SISTEMA \<hará\> | only if present |
| Unwanted | SI \<condición\>, ENTONCES EL SISTEMA \<hará\> | errors and edge cases |

Well-written example:

> RF-4: SI el nombre ya existe (comparación ignorando mayúsculas y espacios
> exteriores), ENTONCES EL SISTEMA no creará un duplicado e informará del
> conflicto (salida 1).

Poorly written, for contrast:

> ~~RF-4: El sistema debe manejar bien los duplicados y ser rápido.~~
> No EARS pattern, no verifiable criterion, two ideas in one sentence, and an
> unmeasurable adjective.

## When reviewing an existing spec

If the user asks to review instead of create, do not rewrite: **detect and list**,
numbered, in four blocks — (1) ambiguities, (2) contradictions between
requirements, (3) uncovered edge cases, (4) conflicts with the constitution.
Write that review in Spanish. Do not propose solutions until asked.
