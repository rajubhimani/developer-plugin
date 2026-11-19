# Architecture

## Layers

```text
web ──► service ──► domain
adapter ──► service (implements the port) ──► domain
```

| Package | Holds | May import | Must not import |
|---|---|---|---|
| `web` | Routes, request and response records, the error format | service, domain | adapter |
| `service` | Use cases and the ports (interfaces) they need | domain | web, adapter |
| `domain` | Business rules as plain Java | the JDK | Spring, any storage or web library |
| `adapter` | Storage and client code that implements a port | domain, service (for the port) | web |

## Rules

- A controller parses input, calls one service method and shapes the response. Rules do not
  live in controllers.
- A service depends on a port (an interface) it defines; Spring injects the adapter.
- API records and domain types are separate; convert at the edge.
- Errors leave the service as domain exceptions; `ApiExceptionHandler` turns them into
  problem-details responses with no stack trace.
- Constructor injection only. Configuration comes from environment variables with defaults
  in `application.yml`; in a cluster the same names come from a ConfigMap and a Secret.
- Only `health` is exposed by the actuator; liveness and readiness probes are enabled.
  Graceful shutdown is on, with a timeout shorter than the pod's grace period.

## Storage

`InMemoryItemRepository` is for the first run and tests. Add a database adapter that
implements `ItemRepository`, and run schema changes with a migration tool (see the
database-migrations skill), never with automatic schema updates in production.

## Decisions

Record significant choices as short decision records in `docs/decisions/`.
