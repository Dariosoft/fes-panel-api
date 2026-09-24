---
name: spec-generator
description: Use this skill when the user asks to create, write, or review a feature specification (spec). It guides a requirements interview and produces a spec.md following the team template. Generated specs are always written in Spanish.
---

# Spec generator

Turn a vague idea into an agreed specification. The spec is the
contract: if something is not here, it is not implemented.

## Language of the spec

Write the entire `spec.md` in **Spanish**: section titles, placeholders
filled in, user stories, EARS requirements, notes, and
`[NECESITA ACLARACIÓN]` markers. Do not mix English into the spec body.
Copy headings and EARS patterns from `spec-template.md` as-is.
The interview with the user may use the conversation language; the
written spec must still be Spanish.

## Process

1. **Read the context.** `docs/constitution.md` if it exists, and previous specs
   in `specs/` so you respect conventions and do not contradict what was already agreed.
2. **Interview the user.** Ask questions **ONE at a TIME**, at most 6, waiting
   for an answer before the next one. Focus on edge cases, error behavior,
   and what is out of scope. Do not propose technical solutions: if the
   user asks "how would you do it?", redirect to the WHAT.
   Prioritize questions whose answer changes what needs to be built; skip
   those with an obvious default answer.
3. **Choose the number.** You may receive an implementation number in 3-digit format. 
   If not, look at `specs/` and use the next free number with three digits: `specs/NNN-<name-in-kebab-case>/spec.md` 
   (Only the created folder must be in English).
4. **Write** using `spec-template.md` from this skill, without skipping
   sections. Keep every section title in Spanish as in the template.
   Acceptance criteria **always in EARS notation in Spanish**, numbered
   as RF-1, RF-2, … Each requirement must be verifiable: if you cannot think of
   how to check it, it is poorly written.
5. **Mark what you do not know** as `[NECESITA ACLARACIÓN: pregunta concreta]`.
   Never fill a gap by inventing: a visible gap is information,
   a silent assumption is debt.
6. **Ask for explicit approval** when finished. Do not move on to the plan or write
   code until you have it.

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
