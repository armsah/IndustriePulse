# Architecture Decision Records

This directory contains Architecture Decision Records (ADRs) for IndustriePulse.

ADRs document architectural decisions that materially affect system behavior, scalability, reliability, security, cost, or maintainability.

The goal is to preserve not only **what** was selected, but also **why** it was selected and what trade-offs were accepted.

## ADR Status Values

Each ADR uses one of the following statuses:

* **Proposed** Ã¢â‚¬â€ under evaluation and not yet accepted.
* **Accepted** Ã¢â‚¬â€ current architectural decision.
* **Superseded** Ã¢â‚¬â€ replaced by a newer ADR.
* **Deprecated** Ã¢â‚¬â€ retained for historical context but should no longer guide implementation.

## ADR Format

Each ADR should contain:

```markdown
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

| ADR     | Decision                                                 | Expected phase | Status   |
| ------- | -------------------------------------------------------- | -------------- | -------- |
| ADR-001 | Messaging roles: Event Hubs vs Service Bus vs Event Grid | P2/P5          | Accepted |
| ADR-002 | Event Hubs partition-key strategy                        | P2             | Accepted  |
| ADR-003 | Event Hubs partition count and capacity strategy         | P2             | Accepted  |
| ADR-004 | Consumer hosting model                                   | P3             | Planned  |
| ADR-005 | Checkpointing strategy                                   | P3             | Planned  |
| ADR-006 | Machine current-state store: PostgreSQL vs Cosmos DB     | P4             | Planned  |
| ADR-007 | Idempotency and duplicate-processing strategy            | P4/P5          | Accepted |
| ADR-008 | Hot telemetry store                                      | P4/P7          | Planned  |
| ADR-009 | Maintenance command retry and DLQ policy                 | P5/P6          | Planned  |
| ADR-010 | Replay isolation strategy                                | P7             | Planned  |
| ADR-011 | Container Apps deployment topology                       | P8             | Planned  |
| ADR-012 | Observability and processing-lag measurement             | P9             | Planned  |
| ADR-013 | Network and private-access architecture                  | P11            | Planned  |

This list is intentionally provisional. ADR numbers should be assigned when a decision is actually started rather than creating empty ADR files in advance.

## Current State

ADR-001 has been accepted and establishes the messaging responsibilities for IndustriePulse:

* **Azure Event Hubs** is the authoritative transport for high-volume machine telemetry.
* **Azure Service Bus** is reserved for reliable maintenance commands and workflow messages requiring queue, retry, DLQ, and re-drive semantics.
* **Azure Event Grid** remains optional and outside the core telemetry and maintenance-command paths.

ADR-002 has been accepted and selects **`machineId` as the Event Hubs partition key**. This preserves machine-scoped ordering and provides substantially higher partition-key cardinality than `siteId`. The decision is supported by deterministic distribution analysis over the 5,000-machine reference inventory.

P0 establishes workload assumptions and non-functional requirements in [`../nfr.md`](../nfr.md).

ADR-003 has been accepted and selects **8 telemetry partitions**, **1-day Event Hubs retention**, and **1 Standard throughput unit for normal development**. Higher capacities are deliberately temporary: 2 TUs for the 1,000-events-per-second Azure reference validation, 3 TUs for a 2,000-events-per-second application benchmark, and 5 TUs as the current 4,000-events-per-second reference-production planning value.

With the three P2 messaging ADRs accepted, P2 can proceed to the corresponding Terraform infrastructure.

ADR-004 has been accepted and selects a **.NET Worker Service** for the telemetry consumer. The worker uses Azure Event Hubs `EventProcessorClient` for partition ownership, processing, and checkpoint coordination.

ADR-005 has been accepted and defines **processing-before-checkpoint semantics**. Successful processing is checkpointed, while a processing failure blocks further checkpoint advancement for that partition during the process lifetime so later events cannot move the durable checkpoint past failed work.

ADR-006 has been accepted and selects **Azure Cosmos DB for NoSQL** for the current machine-state projection. Each machine is represented by one document using `machineId` as both the document identity and `/machineId` partition key. State advances only when an event has a newer `sequence`, preventing duplicate, late, or out-of-order telemetry from regressing current state.

P4 implements this decision through a repository abstraction, Cosmos-backed projection from the telemetry consumer, and an ASP.NET Core current-state API.

ADR-007 has been accepted for P5. Maintenance commands use deterministic identities derived from `eventId` and `ruleId`, rules run only when machine state advances, and the Service Bus queue uses duplicate detection. The decision explicitly retains at-least-once semantics and documents the non-atomic Cosmos DB-to-Service Bus consistency gap for future outbox hardening.
ADR-009 has been accepted for P6. Maintenance-command failures can be inspected in the native Service Bus dead-letter subqueue and selectively re-driven after operator review. Re-drive preserves the original business identity while using a deterministic replacement broker `MessageId` so the intentional recovery is not suppressed by the queue duplicate-detection window. The operation sends the replacement before completing the DLQ message and does not claim atomic or exactly-once delivery.
- [ADR-010: Replay isolation](ADR-010-replay-isolation.md)
