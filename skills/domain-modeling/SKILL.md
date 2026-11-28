---
name: domain-modeling
description: "Layers, ports and adapters, DDD, only where the domain is complex. Use when structuring business logic or reviewing over-layered code."
metadata:
  verified: "2026-11-19"
---

# Domain modelling and layers

Ports and adapters, clean layers and domain-driven design cost code: entities,
ports, adapters, mappers. They pay off only when the business rules are complex
and long-lived. Use them for the core and plain code for the rest.

## Decide first

Ask: *would the domain code still make sense with the database deleted?*

- **Yes, there are real rules** (pricing, eligibility, state machines, money):
  model the domain apart from storage and frameworks.
- **No, the work is queries and forms:** keep it plain. A thin handler, a query
  and a table are fine. Extra layers separate nothing.
- **Prototype, script, migration, batch job:** keep it plain.

Mix in one project: a modelled core (for example billing) beside plain CRUD
modules.

## When you do model the domain

1. **Name things in the users' words.** One term per concept, the same in code,
   docs and tests. Keep a short glossary in the project docs.
2. **Dependencies point inward.** Domain code imports nothing from the web
   framework, the ORM or the cloud SDK.
3. **Ports are small interfaces the domain defines;** adapters (database, queue,
   HTTP client) implement them at the edge.
4. **Put rules in the domain, not the handler.** A rule that lives in a
   controller will be copied into the next controller.
5. **Value objects for values** (money, email, date range): validated once at
   creation, immutable, compared by value.
6. **Keep each transaction inside one aggregate** (one consistent cluster of
   data with one entry point). Refer to other aggregates by id.
7. **Validate at the boundary, trust inside.** Parse raw input into domain types
   once; do not re-check everywhere.
8. **Test the domain without infrastructure.** If a domain test needs a database,
   the boundary is in the wrong place.

## Smells

- **Anemic model:** all behaviour in services, entities only hold fields, and the
  same rule is written in three services.
- **Leaky layers:** database rows or HTTP types passed into the domain.
- **Mapper sprawl:** a mapping layer between identical shapes.
- **Premature bounded contexts:** splitting by guess. Split on evidence (see
  `architecture-monolith-vs-services`).

## Related

`design-patterns` for the small-scale choices, `api-design` for the boundary,
`database-migrations` for storage changes.
