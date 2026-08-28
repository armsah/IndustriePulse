# Architecture Decision Records

This directory contains Architecture Decision Records (ADRs) for IndustriePulse.

ADRs document architectural decisions that materially affect system behavior, scalability, reliability, security, cost, or maintainability.

The goal is to preserve not only **what** was selected, but also **why** it was selected and what trade-offs were accepted.

## ADR Status Values

Each ADR uses one of the following statuses:

* **Proposed** — under evaluation and not yet accepted.
* **Accepted** — current architectural decision.
* **Superseded** — replaced by a newer ADR.
* **Deprecated** — retained for historical context but should no longer guide implementation.

## ADR Format

Each ADR should contain:

```markdown id="7q0ltp"
# ADR-NNN: Decision title

## Status

Proposed | Accepted | Superseded | Deprecated

## Context

What problem or architectural question requires a decision?

## Decision Drivers

What requirements, constraints, measurements, or risks influence the decision?

## Options Considered

What realistic alternatives were evaluated?

## Decision

What was selected?

## Rationale

Why was this option selected?

## Consequences

### Positive

What does the decision enable or simplify?

### Negative

What costs, limitations, or risks does it introduce?

## Validation

How will the decision be validated through implementation, testing, benchmarking, or operational evidence?

## References

Relevant documentation, benchmark results, or related ADRs.
```

## ADR Principles

IndustriePulse ADRs should follow these principles:

1. Decisions should be based on explicit requirements or measured evidence where practical.
2. Azure services should be selected according to their messaging, storage, processing, and operational semantics rather than product familiarity.
3. Cost is a first-class architectural constraint for the development environment.
4. Calculated production sizing must be clearly distinguished from executed benchmarks.
5. Decisions may be revised when later benchmark results contradict initial assumptions.
6. Significant distributed-system behavior should be visible in ADRs rather than buried only in source code.

## Planned ADRs

The following ADRs are expected as the project evolves.

| ADR     | Decision                                                 | Expected phase | Status  |
| ------- | -------------------------------------------------------- | -------------- | ------- |
| ADR-001 | Messaging roles: Event Hubs vs Service Bus vs Event Grid | P2/P5          | Planned |
| ADR-002 | Event Hubs partition-key strategy                        | P2             | Planned |
| ADR-003 | Event Hubs partition count and capacity strategy         | P2             | Planned |
| ADR-004 | Consumer hosting model                                   | P3             | Planned |
| ADR-005 | Checkpointing strategy                                   | P3             | Planned |
| ADR-006 | Machine current-state store: PostgreSQL vs Cosmos DB     | P4             | Planned |
| ADR-007 | Idempotency and duplicate-processing strategy            | P4/P5          | Planned |
| ADR-008 | Hot telemetry store                                      | P4/P7          | Planned |
| ADR-009 | Maintenance command retry and DLQ policy                 | P5/P6          | Planned |
| ADR-010 | Replay isolation strategy                                | P7             | Planned |
| ADR-011 | Container Apps deployment topology                       | P8             | Planned |
| ADR-012 | Observability and processing-lag measurement             | P9             | Planned |
| ADR-013 | Network and private-access architecture                  | P11            | Planned |

This list is intentionally provisional. ADR numbers should be assigned when a decision is actually started rather than creating empty ADR files in advance.

## Current State

No architectural ADR has been accepted yet.

P0 establishes workload assumptions and non-functional requirements in [`../nfr.md`](../nfr.md).

Architecture decisions will be recorded when their implementation phase provides sufficient requirements, alternatives, and evidence.
