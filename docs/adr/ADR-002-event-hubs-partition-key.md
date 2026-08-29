# ADR-002: Event Hubs Partition-Key Strategy
* **Status:** Accepted
* **Date:** 2026-08-29
* **Phase:** P2
* **Related:** ADR-001 Messaging Roles, ADR-003 Event Hubs Partition Count and Capacity Strategy

## Context

IndustriePulse uses Azure Event Hubs as the authoritative transport for machine telemetry.

The initial reference workload contains 5,000 machines across five manufacturing sites, producing approximately 1,000 telemetry events per second.

Telemetry processing requires:
* ordering scoped to an individual machine rather than global ordering;
* machine sequence numbers for detecting gaps, duplicates, and late events;
* horizontal processing across Event Hubs partitions;
* balanced partition utilization across thousands of machines;
* deterministic machine affinity so events for one machine remain in the same logical stream;
* no requirement for site-wide ordering.

Azure Event Hubs guarantees ordering within a partition rather than across an entire event hub.

When a partition key is supplied, Event Hubs hashes that key and maps events with the same key to the same partition. A high-cardinality key can therefore provide both logical stream affinity and distribution across partitions.

The project must choose the partition key before Event Hubs infrastructure is provisioned.

## Decision

IndustriePulse will use **`machineId` as the Azure Event Hubs partition key for live machine telemetry**.

The producer will supply the machine identifier as the logical partition key and will not select Event Hubs partition IDs directly.

All telemetry events belonging to the same machine therefore share a partition-key stream.

This matches the application's consistency boundary because sequence validation, duplicate detection, gap detection, late-event handling, and current-machine-state processing are all machine-scoped operations.

No global or site-wide ordering guarantee is required.

## Candidate Strategies

### `machineId`

Selected.

Advantages:
* provides machine-level partition affinity;
* supports machine-scoped event ordering;
* aligns with the telemetry `sequence` field;
* provides high key cardinality;
* distributes thousands of independent machine streams across available partitions;
* allows different machines to be processed in parallel.

A disproportionately high-volume machine could still contribute to a hot partition, but the IndustriePulse reference workload currently assigns approximately equal telemetry frequency to each machine.

### `siteId`

Rejected.

The initial architecture has five sites, so `siteId` provides only five possible partition keys.

This creates poor partition-key cardinality and can leave partitions unused while concentrating an entire site's telemetry into one partition.

IndustriePulse also has no requirement for strict site-wide event ordering, so the concentration would provide no useful consistency guarantee.

### No partition key

Rejected for the primary telemetry stream.

Allowing Event Hubs to distribute telemetry without a stable machine partition key can improve generic distribution, but it removes the machine affinity required by the application's ordering model.

Events for one machine could be assigned to different partitions, making partition ordering insufficient for machine-scoped sequence processing.

### Direct partition ID

Rejected.

The producer should express the logical relationship between events through `machineId`, not depend on a physical Event Hubs partition number.

Direct partition targeting would unnecessarily couple producers to the configured partition topology and reduces the availability benefits provided by service-managed partition assignment.

## Local Distribution Evidence

A deterministic local analysis was executed using the existing IndustriePulse 5,000-machine inventory.

The analysis compares `machineId` and `siteId` under modeled partition counts of 4, 8, and 16.

The local model uses SHA-256 followed by modulo partition count to create deterministic assignments.

This hash function is **not intended to reproduce Azure Event Hubs' internal partition-key hash implementation**. The experiment measures the cardinality and expected distribution characteristics of the candidate application keys.

Measured results:

| Key         | Partitions | Used partitions | Minimum machines | Maximum machines | Max / mean |    CV |

| ----------- | ---------: | --------------: | ---------------: | ---------------: | ---------: | ----: |

| `machineId` |          4 |               4 |            1,219 |            1,296 |      1.037 | 0.026 |

| `siteId`    |          4 |               3 |                0 |            3,000 |      2.400 | 0.872 |

| `machineId` |          8 |               8 |              581 |              654 |      1.046 | 0.035 |

| `siteId`    |          8 |               4 |                0 |            2,000 |      3.200 | 1.114 |

| `machineId` |         16 |              16 |              282 |              340 |      1.088 | 0.052 |

| `siteId`    |         16 |               4 |                0 |            2,000 |      6.400 | 1.865 |

The experiment demonstrates that the 5,000-value `machineId` key space provides substantially better distribution characteristics than the five-value `siteId` key space.

At eight modeled partitions, `machineId` used every partition with a coefficient of variation of 0.035, whereas `siteId` used only four partitions and produced a coefficient of variation of 1.114.

The analyzer is deterministic and covered by automated tests.

The complete Python simulator test suite passed with 45 tests after the partition-analysis functionality was introduced.

## Ordering Semantics

The application relies only on ordering for events belonging to the same machine.

Using `machineId` as the partition key means events published with the same machine identifier are mapped to the same Event Hubs partition.

Within the consumer, the telemetry `sequence` field remains authoritative for detecting:
* duplicates;
* sequence gaps;
* late events;
* invalid attempts by old telemetry to overwrite newer machine state.

Partition ordering does not remove the need for these application-level controls because IndustriePulse uses at-least-once processing and explicitly tests duplicate and late-event scenarios.

## Partition-Count Implication

The partition-key decision is related to, but separate from, the number of Event Hubs partitions.

ADR-003 will determine the initial partition count using throughput, consumer parallelism, growth, operational complexity, and cost considerations.

Because the reference implementation uses Event Hubs Standard, the partition count must be chosen deliberately when the event hub is created rather than relying on later dynamic partition expansion.

The application will therefore treat the partition count as an infrastructure design decision rather than an automatically elastic parameter.

## Consequences

### Positive
* Machine-level ordering matches the application's actual consistency requirement.
* Machine sequence processing remains partition-local.
* Thousands of machine identifiers provide high partition-key cardinality.
* Consumers can process different machines concurrently.
* Producers remain independent of physical partition IDs.
* The decision scales naturally from the initial 5,000-machine reference workload toward larger machine populations.
* The partition-key choice is supported by deterministic local evidence rather than architectural intuition alone.

### Negative
* A single extremely high-volume machine cannot be split across multiple partitions while preserving its machine-level ordering.
* Distribution ultimately depends on Event Hubs' own partition-key mapping rather than the local SHA-256 model used for analysis.
* Changing the logical partition key in the future would alter machine-stream routing and require explicit migration planning.
* Partition count must still be sized independently; a good key does not compensate for insufficient Event Hubs capacity.

## Validation

ADR-002 is satisfied when:
* telemetry producers publish using `machineId` as the Event Hubs partition key;
* producers do not directly assign Event Hubs partition IDs;
* consumer logic assumes machine-scoped rather than global ordering;
* sequence-based duplicate, gap, and late-event handling remains application controlled;
* Terraform partition count is decided separately by ADR-003;
* integration testing later verifies that events for a single machine remain partition-affine in the deployed Event Hub.

## References
* Microsoft Learn: Azure Event Hubs scalability and partitioning guidance.
* Microsoft Learn: Azure Event Hubs reliability guidance.
* Microsoft Azure SDK documentation for Event Hubs producer partition keys.
* IndustriePulse non-functional requirements in `docs/nfr.md`.
* IndustriePulse deterministic partition analysis in `simulator/python`.



