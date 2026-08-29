# ADR-003: Event Hubs Partition Count and Capacity Strategy

* **Status:** Accepted

* **Date:** 2026-08-29

* **Phase:** P2

* **Related:** ADR-001 Messaging Roles, ADR-002 Event Hubs Partition-Key Strategy

## Context

IndustriePulse uses Azure Event Hubs Standard as the authoritative transport for machine telemetry.

ADR-002 selects `machineId` as the telemetry partition key. This ADR determines the initial Event Hub partition count, development throughput-unit configuration, reference-workload sizing, and retention configuration.

The P0 workload assumptions are:

* 5,000 machines in the initial reference workload;

* one event per machine every five seconds;

* approximately 1,000 ingress events per second;

* approximately 350 bytes per event as a conservative planning payload;

* approximately 350 KB/s of application payload at the reference workload;

* a 2,000-events-per-second higher-load test target;

* a future reference-production scenario of 20,000 machines and approximately 4,000 events per second;

* one day of Event Hubs retention;

* multiple independent downstream consumers over time;

* strict cost control for the portfolio environment.

The event-rate quota is more restrictive than payload bandwidth for these workloads.

At a 350-byte planning payload:

* 1,000 events/s is approximately 0.35 MB/s;

* 2,000 events/s is approximately 0.70 MB/s;

* 4,000 events/s is approximately 1.40 MB/s.

Azure Event Hubs Standard throughput units provide aggregate namespace capacity. Each throughput unit currently provides up to:

* 1 MB/s ingress, subject also to a maximum of 1,000 ingress events, management operations, or control API calls per second;

* 2 MB/s egress, subject also to the Event Hubs egress event-rate quota;

* 84 GB of event-retention storage allowance.

Throughput-unit capacity applies across the namespace rather than independently to each partition.

The number of partitions is a separate design dimension from throughput-unit capacity.

## Decision

IndustriePulse will create the primary telemetry Event Hub with:

* **8 partitions**;

* **1-day message retention**;

* **Event Hubs Standard**;

* **1 throughput unit for normal development deployment**;

* **Capture disabled during P2**;

* **auto-inflate disabled initially**.

Higher throughput-unit counts will be applied only for specific Azure validation or benchmark runs.

The project will distinguish clearly between:

1\. capacity normally deployed for low-cost development;

2\. capacity temporarily deployed for executed Azure load tests;

3\. mathematical/reference production sizing.

## Partition Count

The primary telemetry Event Hub will use **8 partitions**.

This decision is based on ordering, parallelism, measured key distribution, future growth, and operational simplicity.

ADR-002 measured the 5,000-machine inventory using the selected `machineId` partition-key strategy.

For eight modeled partitions, the local deterministic analysis produced:

* all 8 partitions used;

* minimum 581 machines per partition;

* maximum 654 machines per partition;

* maximum-to-mean ratio 1.046;

* coefficient of variation 0.035.

The local SHA-256 model does not reproduce Azure Event Hubs' internal partition-key hash implementation, but it demonstrates that the selected 5,000-value key space has sufficient cardinality to distribute effectively across eight partitions.

Eight partitions also permit up to eight active partition-owning consumer instances per consumer group before additional instances become idle.

That provides sufficient parallelism for the initial reference workload and leaves room for later consumer scale-out without selecting the maximum Standard partition count unnecessarily.

## Why Not Fewer Partitions

### Four partitions

Four partitions would be sufficient for the initial event rate from a pure throughput perspective.

It is rejected because it unnecessarily restricts future consumer parallelism.

The 20,000-machine reference-production scenario reaches approximately 4,000 events per second, and later phases explicitly test downstream slowdown, backlog accumulation, and recovery.

Eight partitions provide a better processing-parallelism margin while introducing little additional architectural complexity.

### One or two partitions

Rejected.

These configurations would preserve machine-key ordering but would constrain consumer parallelism and make a single slow partition owner responsible for a large fraction of the telemetry workload.

They provide no meaningful cost advantage because Standard Event Hubs pricing is based primarily on throughput units rather than charging independently for each ordinary partition.

## Why Not More Partitions

### Sixteen or thirty-two partitions

Rejected for the initial implementation.

The P2.2 local distribution experiment demonstrates that `machineId` could distribute effectively across sixteen modeled partitions, but the current workload does not require that level of consumer concurrency.

More partitions increase checkpointing, partition ownership, diagnostics, and operational surface area.

Selecting the Standard maximum solely because partitions do not independently incur throughput-unit charges would optimize for theoretical expansion rather than the demonstrated workload.

Eight partitions provide a deliberate middle ground between future parallelism and operational simplicity.

## Standard-Tier Immutability

For Event Hubs Standard, the partition count cannot be dynamically increased after the event hub has been created.

This makes the initial partition count an important infrastructure decision.

The eight-partition choice therefore includes growth headroom rather than sizing only for the minimum P2 development workload.

If IndustriePulse eventually requires materially more partition-level concurrency than eight partitions provide, migration to a newly created Event Hub or reassessment of the Event Hubs tier would be required.

That migration must preserve the machine-ordering guarantees established by ADR-002.

## Throughput-Unit Sizing

### Normal development: 1 TU

The continuously configured development namespace will use **1 throughput unit**.

This is the minimum normal development capacity and is intentionally cost constrained.

It is suitable for:

* infrastructure validation;

* producer connectivity tests;

* low-volume smoke tests;

* consumer/checkpoint development;

* functional integration testing.

It must not be presented as evidence that the production/reference workload has sufficient headroom.

The P0 reference workload of approximately 1,000 events per second is exactly at the documented per-TU ingress event-rate limit.

Therefore, sustained execution of the full 1,000-events-per-second reference workload on one TU would deliberately operate at the quota boundary and is not the selected validation configuration.

## Reference Azure Validation: 2 TUs

When an Azure test needs to execute the approximately **1,000-events-per-second** reference workload, the namespace should temporarily use **2 TUs**.

The theoretical ingress requirement based only on event rate is one TU.

Two TUs are selected for executed validation because they avoid designing the test around the exact 1,000-events-per-second single-TU ceiling and provide capacity for management/control operations, short bursts, and normal variation.

After the test, capacity should return to the normal low-cost development setting or the infrastructure should be destroyed when no longer required.

## Higher-Load Benchmark: 3 TUs

The P0 higher-load target is approximately **2,000 events per second**.

The theoretical minimum based on the documented ingress event-rate quota is:

2,000 events/s ÷ 1,000 events/s/TU = 2 TUs.

The executed benchmark configuration will use **3 TUs** when the goal is to test application behavior at 2,000 events per second rather than intentionally test Event Hubs throttling.

This provides 50% event-rate headroom over the target workload.

A separate experiment may intentionally run the workload against insufficient TU capacity when testing throttling or backpressure behavior.

Such an experiment must be labelled accordingly and must not be confused with capacity validation.

## Reference-Production Sizing: 5 TUs

The P0 reference-production scenario contains:

* 20,000 machines;

* approximately 4,000 ingress events per second;

* approximately 1.4 MB/s of application payload at the 350-byte planning size.

The theoretical ingress capacity requirements are:

Event-rate requirement:

4,000 events/s ÷ 1,000 events/s/TU = 4 TUs.

Payload-bandwidth requirement:

1.4 MB/s ÷ 1 MB/s/TU = 1.4 TUs.

The event-rate quota therefore dominates.

Four TUs are the mathematical minimum based on the current assumptions.

The reference-production design uses **5 TUs** as its planning value, providing approximately 25% event-rate capacity above the 4,000-events-per-second target.

This is a sizing calculation, not a commitment to keep five TUs provisioned in the portfolio environment.

The production figure must be revisited using measured encoded Event Hubs message sizes, actual consumer topology, burst characteristics, and benchmark evidence before any real production deployment.

## Egress Considerations

Ingress is not the only throughput constraint.

Independent Event Hubs consumer groups can each read the telemetry stream, so aggregate egress increases as additional consumers independently process the same events.

Later phases introduce consumers for live state, rules, persistence, replay/diagnostics, and observability.

Capacity validation must therefore inspect both ingress and egress metrics.

At the initial stages, two TUs provide substantially more egress headroom than the one-TU development configuration.

P9 and P10 will measure actual processing lag, consumer throughput, and dependency behavior rather than assuming ingress sizing alone proves end-to-end capacity.

## Retention

The primary telemetry Event Hub will initially use **1 day of retention**.

This matches the P0 requirement.

At the 350-byte planning payload, the reference workload produces approximately 30.24 GB of application payload per day.

One Standard TU currently includes an Event Hubs retention-storage allowance substantially above this raw application-payload estimate.

However, the application-payload calculation is not treated as an exact Azure storage-billing prediction because service encoding and storage accounting may differ from the simulator's serialized payload.

Longer history belongs in the project's hot and cold telemetry stores rather than increasing Event Hubs retention without a demonstrated replay requirement.

## Auto-Inflate

Auto-inflate will be **disabled initially**.

The portfolio environment prioritizes predictable cost, and the normal development workload does not require automatic TU growth.

Capacity changes for P2 through P10 should therefore be explicit and tied to a documented test.

Auto-inflate may be reconsidered for a production-oriented deployment where availability requirements justify automatically increasing throughput capacity during unexpected ingress growth.

If enabled later, it must use an explicit maximum TU limit to bound cost.

## Capture

Event Hubs Capture remains **disabled during P2**.

Capture is a separately priced Standard-tier capability and is not required to validate Event Hubs provisioning, partitioning, producer connectivity, or checkpointing.

It will be reconsidered in P7 when the replay and cold-storage implementation provides a concrete requirement.

## Cost-Control Policy

The following capacity rules apply to the portfolio environment:

1\. Keep normal development capacity at one Standard TU.

2\. Do not continuously publish the complete 5,000-machine workload to Azure.

3\. Use local deterministic simulation for workloads that do not require Azure behavior.

4\. Temporarily increase TUs only when a test requires documented Azure throughput evidence.

5\. Return capacity to one TU after a temporary test if the namespace remains deployed.

6\. Destroy temporary infrastructure when it is no longer needed.

7\. Keep Capture disabled until its P7 requirement is evaluated.

8\. Keep auto-inflate disabled unless a later accepted decision requires it.

9\. Record the TU configuration used by every throughput benchmark.

10\. Keep executed benchmark results separate from mathematical production sizing.

## Consequences

### Positive

* Eight partitions provide useful consumer scale-out headroom.

* The selected `machineId` key has demonstrated sufficient cardinality for the partition topology.

* Partition count does not need to change between low-cost development and higher-throughput tests.

* One-TU normal development minimizes ongoing Azure cost.

* Higher-load tests can temporarily scale namespace capacity without changing the Event Hub partition topology.

* Reference capacity calculations explicitly account for the ingress event-rate limit rather than only payload bandwidth.

* Development, benchmark, and production-reference capacity are clearly separated.

* One-day retention matches the stated architectural requirement.

* Optional paid features remain disabled until required.

### Negative

* Eight partitions create more consumer/checkpoint state than the smallest possible topology.

* Standard-tier partition count is immutable, so changing it later would require migration or tier reassessment.

* One TU cannot provide comfortable headroom for sustained execution of the 1,000-events-per-second reference workload.

* Executing reference and benchmark loads in Azure requires temporary TU increases and therefore additional short-lived cost.

* Production sizing will require revision if event size, event frequency, consumer count, or burst behavior changes.

## Validation

ADR-003 is satisfied when:

* Terraform creates the telemetry Event Hub with eight partitions;

* Event Hubs Standard is used;

* normal development capacity is one TU;

* retention is configured for one day;

* Capture is disabled in P2;

* auto-inflate is disabled initially;

* the deployed topology does not include unnecessary P2 messaging resources;

* later Azure throughput tests record their configured TU count;

* P10 distinguishes executed benchmark evidence from reference-production calculations;

* actual Azure metrics are used to revise capacity assumptions when evidence becomes available.

## References

* Microsoft Learn: Azure Event Hubs quotas and limits.

* Microsoft Learn: Azure Event Hubs scalability.

* Microsoft Learn: Compare Azure Event Hubs tiers.

* Microsoft Azure Event Hubs pricing.

* IndustriePulse non-functional requirements in `docs/nfr.md`.

* ADR-001: Messaging Roles — Event Hubs, Service Bus, and Event Grid.

* ADR-002: Event Hubs Partition-Key Strategy.




