---
name: writing-style
description: "Plain-language rules for docs, READMEs, reports, pull request descriptions, commit messages and agent instructions. Use when writing or editing any prose a person or a model will read."
verified: 2026-11-17
---

# Writing style

Write for a capable reader who is new to the topic and has none of your
context: an engineer joining the project, or a model starting a fresh session.
If they would have to ask what something means, the text is not done.

## Rules

1. **Lead with the point.** The first sentence says what this is or what to do.
2. **Short sentences, one idea each.** Split anything long.
3. **Plain words.** `use`, not `utilize`. `because`, not `due to the fact that`.
4. **Be specific.** A number, path, command or example beats an adjective.
   "Retries three times, then asks a person" beats "robust retry handling".
5. **Say it once.** Each fact has one home; link to it elsewhere.
6. **Describe the current state.** Reasons belong in a decision record, history
   in git.
7. **Use emphasis rarely.** No all-caps, no stacked warnings.
8. **Expand acronyms on first use** in each document, as `ACRONYM (Full Form)`.
   Skip the universally known ones (API, URL, JSON, SQL, HTTP, CLI, UI).
9. **Use placeholders in examples** (`<project>`, `<slug>`), never real names.
10. **Name things descriptively and keep the name.** Do not coin labels readers
    must decode.

## Structure

- One topic per file. Headings are labels a reader would search for.
- Tables for facts of one shape, numbered lists for steps, bullets for sets,
  prose for reasoning.
- Paths, commands and identifiers in backticks.
- A report to a person opens with the decision: where things stand, what they
  must decide, then the detail. Name no internal check codes.

## Instructions for agents

Write plain imperatives ("Run the tests before reporting"), give the reason in
one clause when it changes what the reader does, and prefer one example to a
paragraph of rules.
