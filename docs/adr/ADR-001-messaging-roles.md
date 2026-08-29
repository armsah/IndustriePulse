# ADR-001: Messaging Roles — Event Hubs, Service Bus, and Event Grid

* **Status:** Accepted
* **Date:** 2026-08-29
* **Phase:** P2
* **Decision owners:** IndustriePulse project
* **Related:** ADR-002 Event Hubs partition-key strategy, ADR-003 Event Hubs partition and capacity sizing

## Context

IndustriePulse processes industrial telemetry from CNC machines, compressors, and robots across multiple manufacturing sites.

The initial reference workload is:

* 5,000 machines.
* One telemetry event per machine every five seconds.
* Approximately 1,000 telemetry events per second at the reference load.
* A higher test target of approximately 2,000 events per second.
* At-least-once delivery semantics.
* Partition-scoped ordering rather than global ordering.
* Multiple downstream processing concerns over time, including live-state processing, anomaly detection, storage, replay, and observability.
* Maintenance commands and notifications that require reliable queue semantics, bounded retries, dead-letter handling, and re-drive.
* Replayable telemetry history.
* Strict cost control for the portfolio/development environment.

Azure provides several messaging services that overlap superficially but have materially different semantics.

The architecture must therefore distinguish between:

1. a high-throughput append-only telemetry stream;
2. reliable business/workflow commands;
3. lightweight discrete integration events.

Using one messaging product for all three concerns would obscure their different delivery, ordering, retry, retention, and consumption semantics.

Cost is an explicit architectural constraint. The project must demonstrate production-oriented design without keeping unnecessary Azure resources running or generating artificial cloud traffic solely to claim scale.

## Decision

IndustriePulse assigns distinct roles to Azure Event Hubs, Azure Service Bus, and Azure Event Grid.

### Azure Event Hubs — telemetry event stream

Azure Event Hubs is the authoritative transport for machine telemetry.

Telemetry such as temperature, vibration, pressure, RPM, machine identity, timestamp, sequence, and firmware version is published to an Event Hub.

Event Hubs is selected because the telemetry workload is an ordered, partitioned, high-throughput stream that must support independent consumers and replay within the configured retention period.

Expected Event Hubs consumers can include:

* live machine-state processing;
* anomaly/rule processing;
* telemetry persistence;
* replay or diagnostic consumers;
* observability and benchmark workloads.

No global telemetry ordering is required. Ordering guarantees and partition-key selection are handled separately in ADR-002.

Partition count and throughput-unit sizing are handled separately in ADR-003.

### Event Hubs development SKU

The reference implementation will use **Event Hubs Standard**, initially configured with the minimum practical throughput capacity.

Standard is preferred to Basic because the project roadmap requires multiple independent consumer groups and later Event Hubs Capture experimentation.

The initial development deployment will use **1 throughput unit** unless a specific benchmark requires more.

The 1-TU development configuration is a cost-control setting and must not be confused with production capacity sizing.

The production/reference sizing calculation remains separate from the Azure resources actually kept running during development.

### Azure Service Bus — maintenance commands and reliable workflow messages

Azure Service Bus is reserved for maintenance commands, notifications, and other workflow messages where queue semantics are required.

Examples include:

* create maintenance work;
* notify a maintenance workflow;
* retry a failed command;
* dead-letter a poison command;
* inspect the dead-letter reason;
* explicitly re-drive a failed command.

Service Bus is not used for the raw telemetry stream.

Raw telemetry volume and replay semantics are better suited to Event Hubs, while Service Bus is intended for reliable command/workflow processing.

Service Bus infrastructure will not be created during P2.

It will be introduced in P5, when its required features and minimum viable pricing tier can be selected from concrete maintenance-workflow requirements.

Application-level idempotency remains required even when messaging infrastructure provides delivery or duplicate-detection features.

### Azure Event Grid — optional integration events

Azure Event Grid is not part of the core telemetry or maintenance-command path.

It may be introduced later for discrete integration notifications where push-based event routing is useful, for example notifying another component that a resource, export, or other integration-level event occurred.

Event Grid will not be used as the durable telemetry log and will not replace Event Hubs.

Event Grid will not be provisioned unless a later phase introduces a concrete requirement for it.

## Messaging responsibility matrix

| Requirement                          | Event Hubs                 | Service Bus                | Event Grid                   |
| ------------------------------------ | -------------------------- | -------------------------- | ---------------------------- |
| High-volume machine telemetry        | **Primary**                | No                         | No                           |
| Partition-scoped telemetry ordering  | **Yes**                    | Not the selected role      | No                           |
| Independent telemetry consumers      | **Yes**                    | Not the selected role      | Integration subscribers only |
| Telemetry replay                     | **Yes**                    | No                         | No                           |
| Maintenance commands                 | No                         | **Primary**                | No                           |
| Bounded command retries              | No                         | **Yes**                    | Not the selected role        |
| Poison-message/DLQ workflow          | No                         | **Yes**                    | Not the selected role        |
| Command re-drive                     | No                         | **Yes**                    | No                           |
| Lightweight integration notification | Possible but not preferred | Possible but not preferred | **Optional primary role**    |
| Core telemetry persistence transport | **Yes**                    | No                         | No                           |

## Cost-control policy

Cloud cost is part of the architecture rather than an afterthought.

The following rules apply to the portfolio environment:

1. Do not provision Service Bus during P2 because no P2 workload requires it.
2. Do not provision Event Grid unless a concrete integration requirement appears.
3. Begin Event Hubs development with one Standard throughput unit.
4. Run small Azure smoke/integration workloads rather than continuously producing the full 5,000-machine reference workload.
5. Use the deterministic local simulator and mathematical capacity calculations for tests that do not require Azure.
6. Perform higher-volume Azure tests only when they produce specific evidence that cannot be obtained locally.
7. Scale Azure capacity explicitly for such tests and scale it back afterward.
8. Destroy temporary infrastructure when a development session or experiment no longer requires it.
9. Do not claim that a low-cost Azure smoke test demonstrates production throughput; executed benchmarks and calculated production sizing must remain clearly separated.
10. Review optional paid features such as Event Hubs Capture before enabling them.

## Consequences

### Positive

* Telemetry and command workloads use messaging systems aligned with their semantics.
* Telemetry consumers can evolve independently through Event Hubs consumer groups.
* Replay remains a first-class property of the telemetry architecture.
* Maintenance commands gain explicit retry, DLQ, and re-drive semantics when Service Bus is introduced.
* Event Grid does not become an unnecessary dependency in the core data path.
* Azure cost remains bounded during development.
* Local scale evidence is not confused with cloud throughput evidence.
* Future infrastructure decisions can be tested without changing the fundamental messaging model.

### Negative

* The complete system will eventually use more than one messaging product.
* Engineers must understand the delivery semantics of both Event Hubs and Service Bus.
* Application-level idempotency remains necessary because at-least-once processing can create duplicates.
* The low-cost development deployment will not itself demonstrate the full reference-production throughput.
* Event Hubs Standard incurs provisioned throughput-unit charges while the namespace exists, even when traffic is low.

## Alternatives Considered

### Use Service Bus for all telemetry and commands

Rejected.

Telemetry is a high-volume stream consumed independently by several processors and needs replay-oriented semantics. Treating each telemetry sample as a business/workflow queue message would mix stream processing with command processing and would not reflect the intended architecture.

### Use Event Hubs for telemetry and maintenance commands

Rejected.

Event Hubs is appropriate for the telemetry stream, but maintenance commands require explicit queue-oriented lifecycle behavior including retries, poison-message handling, DLQ inspection, and controlled re-drive.

Using Event Hubs for both would force application code to recreate workflow semantics already represented by Service Bus.

### Use Event Grid for the telemetry stream

Rejected.

Event Grid is suited to discrete event distribution and integration notifications, not as the primary durable, partitioned telemetry stream for IndustriePulse.

### Use only Event Hubs Basic to minimize cost

Rejected as the reference architecture.

Basic can reduce capability and cost, but it restricts features needed by the planned architecture, particularly independent consumer-group usage and later Capture experimentation.

Instead, the project uses the minimum practical Standard capacity and controls cost through short-lived deployments and deliberately small development workloads.

### Provision all messaging services at the beginning

Rejected.

Provisioning Event Hubs, Service Bus, and Event Grid before their respective workloads exist would increase both cost and operational surface area without creating useful evidence.

Infrastructure will be introduced phase-by-phase.

## Validation

ADR-001 is satisfied when:

* raw telemetry is assigned only to Event Hubs in the core architecture;
* maintenance workflow messages are assigned to Service Bus;
* Event Grid remains optional and outside the core telemetry path;
* P2 Terraform does not provision Service Bus or Event Grid;
* P2 Event Hubs infrastructure begins with a deliberately minimal development capacity;
* production/reference sizing remains documented separately from deployed low-cost development capacity.

## References

* Microsoft Azure Event Hubs pricing and throughput-unit documentation.
* Microsoft Learn: Event Hubs tier comparison and scalability.
* Microsoft Azure Service Bus pricing and tier documentation.
* Microsoft Azure Event Grid pricing and tier documentation.
* IndustriePulse non-functional requirements in `docs/nfr.md`.
