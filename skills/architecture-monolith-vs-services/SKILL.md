---
name: architecture-monolith-vs-services
description: Choose between a modular monolith and microservices, define module and service boundaries, and avoid a distributed monolith. Use when designing system architecture, deciding whether to split a service, or reviewing service boundaries.
verified: 2026-11-07
---

# Monolith or services

Team-size and cost figures in published guides are rough heuristics from
vendor and community sources. Use them only as prompts for a decision.

## Default

- Start with a **modular monolith**: one deployable unit, with modules that own
  their data and expose a small interface. Most products never need more.
- Split a module into its own service only when there is evidence: a different
  scaling profile, a team that must release on its own schedule, or a hard
  isolation requirement (security, compliance, failure domain).

## Boundaries

- A module or service owns its data. Other parts read it through the interface,
  never by querying its tables.
- Name boundaries by business capability (orders, billing), not by technical
  layer (controllers, repositories).
- Limit the number of calls one user request makes across boundaries.

## Warning signs of a distributed monolith

- Deploying one service requires deploying several others.
- A change in one service needs the same change in several others at once.
- Several services share one database.
- A single request fails when any one of many services is down.

## If you split

- Each service has its own CI/CD pipeline, health checks, logs and dashboards.
- Contracts between services are versioned (see `repo-api-and-ui`).
- Plan for failure: timeouts, retries with limits, and idempotent operations.
