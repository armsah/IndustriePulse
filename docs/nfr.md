# IndustriePulse — Non-Functional Requirements and Workload Model

**Phase:** P0 — Requirements and workload definition  
**Status:** Accepted baseline

## 1. Purpose

This document defines the initial workload model and non-functional requirements for IndustriePulse. These values are design inputs for the simulator, Azure Event Hubs sizing, stream processing, current-state storage, alerting, replay, backpressure tests, observability, and later production-sizing exercises.

The project distinguishes between:

1. **Executed demo workload** — traffic that is actually generated and measured.
2. **Reference production workload** — a calculated sizing scenario used to discuss scale beyond the development budget.

Calculated production figures must never be presented as measured benchmark results.

## 2. Manufacturing topology

The baseline demo models five fictional German manufacturing sites.

| Property | Baseline |
| --- | ---: |
| Sites | 5 |
| Machines per site | 1,000 |
| Total machines | 5,000 |
| Machine types | CNC, compressor, robot |
| Site ID format | `DE-<CITY>-<NN>` |
| Machine ID format | `<TYPE>-<NNN>` |

Example fictional site IDs: `DE-MUC-01`, `DE-BER-01`, `DE-HAM-01`, `DE-FRA-01`, `DE-STR-01`.

## 3. Telemetry workload

Each machine emits one telemetry event every five seconds.

```text
5,000 machines / 5 seconds = 1,000 events/second
```

| Period | Events |
| --- | ---: |
| Second | 1,000 |
| Minute | 60,000 |
| Hour | 3,600,000 |
| Day | 86,400,000 |
| 7 days | 604,800,000 |
| 30 days | 2,592,000,000 |

The baseline ingress target is **1,000 events/second**.

## 4. Event-size planning assumption

The initial telemetry contract is compact JSON and is expected to be approximately 250–300 bytes before transport and storage overhead.

For planning, IndustriePulse uses **350 bytes average per telemetry event** to allow for metadata and schema growth.

| Metric | Approximate value |
| --- | ---: |
| Average event size | 350 bytes |
| Baseline payload rate | 350 KB/s |
| Payload per hour | 1.26 GB |
| Payload per day | 30.24 GB |
| Payload per 7 days | 211.68 GB |
| Payload per 30 days | 907.2 GB |

These are uncompressed application-payload estimates. Actual serialized sizes will be measured during P1/P10.

## 5. Peak and test workload

The architecture must not assume that baseline traffic is the maximum possible traffic.

| Metric | Baseline | Short test peak |
| --- | ---: | ---: |
| Machines | 5,000 | 5,000 |
| Events/second | 1,000 | 2,000 |
| Approx. payload/second | 0.35 MB | 0.70 MB |

The simulator must allow machine count and emission rate to be configured independently.

Throttling during deliberate overload experiments is expected behavior and must be measured rather than hidden.

## 6. Simulator requirements

The Python simulator must support **at least 10,000 virtual devices locally**.

Required configuration inputs:

- deterministic random seed;
- machine count;
- site count;
- reporting interval or event rate;
- simulation duration;
- duplicate-event rate;
- late-event rate;
- malformed-event rate;
- named fault scenario.

Given the same seed and configuration, injected fault behavior must be reproducible.

## 7. Standard fault-injection profile

| Condition | Target |
| --- | ---: |
| Late/out-of-order events | 2% |
| Duplicate events | 1% |
| Malformed events | 0.1% |

These percentages are deliberate engineering test inputs, not claims about real industrial equipment.

## 8. Ordering semantics

IndustriePulse does not require global ordering.

Requirements:

- ordering may only be relied on within an Event Hubs partition;
- telemetry for one machine should normally retain machine-relative ordering;
- every telemetry event contains `eventId`, `timestampUtc`, and a machine-local `sequence`;
- consumers must detect sequence gaps;
- consumers must detect duplicate event IDs or duplicate logical events;
- consumers must explicitly identify late/out-of-order events;
- an older event must not silently overwrite newer current machine state.

The partition-key decision will be recorded separately in an ADR before Event Hubs is provisioned.

## 9. Delivery and idempotency

Telemetry processing assumes **at-least-once delivery**.

Exactly-once transport delivery is not required.

Duplicate processing must not:

- create duplicate maintenance incidents;
- create duplicate maintenance commands;
- incorrectly increment derived counters;
- regress current machine state.

`eventId` is the primary event identity. Additional domain-specific idempotency keys may be introduced where required.

## 10. Event time and late data

The system must distinguish:

- event time;
- ingestion time;
- processing time.

The initial late-event tolerance for rolling telemetry evaluation is **5 minutes**.

Late events remain part of historical telemetry even when they are no longer eligible to replace current state.

## 11. Processing-latency targets

Under normal workload with healthy dependencies:

| Flow | p95 target |
| --- | ---: |
| Ingestion to consumer processing | ≤ 5 s |
| Ingestion to current-state visibility | ≤ 10 s |
| Rule violation to maintenance command creation | ≤ 10 s |
| Current-state API request | ≤ 500 ms |

These are IndustriePulse engineering targets, not Azure service SLA statements.

## 12. Current machine state

The system maintains the latest accepted state for each machine.

Initial capacity: **5,000 machine records**.  
Reference scalability target: **100,000 machine identities without a data-model redesign**.

Current state should include at minimum:

- machine ID;
- site ID;
- machine type;
- latest accepted sequence;
- latest event timestamp;
- last telemetry receipt time;
- latest telemetry values;
- firmware version;
- operational status;
- active alert state.

Current state is derived data and should be reconstructable from sufficient retained source telemetry.

## 13. Query requirements

The operations API must support:

### Machine lookup

Retrieve current state by `machineId`.

Target: **p95 ≤ 500 ms**.

### Site machine list

List machines for a site with filters for:

- machine type;
- operational status;
- active-alert status.

### Active alerts

Filter by:

- site;
- machine;
- severity;
- rule type.

### Recent telemetry

Retrieve bounded recent telemetry for one machine.

Interactive dashboard requirement: **up to 24 hours**.  
Typical visualization window: **15 minutes to 6 hours**.

### Maintenance incidents

Retrieve by machine, site, status, and bounded date range.

## 14. Retention requirements

### Event-stream retention

Initial Event Hubs retention design target: **1 day**.

Event Hubs is the streaming transport and short-term event log, not the long-term telemetry archive.

### Hot/query-optimized telemetry

Initial hot retention target: **7 days**.

Primary use cases:

- recent dashboard graphs;
- troubleshooting;
- inspecting telemetry surrounding alerts;
- comparing current and recent behavior.

### Cold telemetry

Initial architectural cold-retention target: **30 days** in Blob Storage or Data Lake.

At the planning workload this represents roughly **907 GB of uncompressed application payload**, so the development environment is not required to run continuously at full target scale for 30 days.

Short benchmark datasets are acceptable during development. Retention cost must be estimated before prolonged cloud execution.

## 15. Alert requirements

Initial production alerting is rule-based.

Example rule classes:

- high temperature;
- sustained vibration;
- abnormal pressure;
- excessive RPM;
- missing telemetry;
- sequence gaps.

Initial severity values:

- `Info`
- `Warning`
- `Critical`

An alert contains at minimum:

- alert ID;
- machine ID;
- site ID;
- rule ID;
- rule version;
- severity;
- triggering event ID;
- event timestamp;
- detection timestamp;
- measured values;
- thresholds;
- alert status.

One continuous fault condition should result in one logical active incident unless a rule explicitly requires otherwise.

## 16. Missing telemetry

A machine becomes an offline/missing-telemetry candidate after **30 seconds** without telemetry.

At the baseline five-second reporting interval, that corresponds to approximately six missed reporting intervals.

The threshold must be configurable.

## 17. Maintenance-command reliability

Maintenance commands require queue/workflow semantics.

Requirements:

- at-least-once processing;
- idempotent handlers;
- bounded retries;
- failed commands moved to a dead-letter queue;
- failure reason visible to operators;
- manual re-drive supported;
- successful re-drive must not duplicate previously completed work.

The concrete Service Bus retry count is deferred to the Service Bus implementation phase.

## 18. Replay requirements

Historical telemetry must be replayable.

Requirements:

1. Replay must not mutate live state by default.
2. Replay must identify the processor/rule version used.
3. Replay must use an isolated consumer/output path.
4. Reprocessing the same deterministic input through the same deterministic rules should produce the same logical result.
5. Replay must not duplicate live maintenance alerts or incidents.
6. Replay progress and failures must be observable.

Initial isolated replay performance target: **at least 5,000 events/second** for a local/offline benchmark.

Cloud replay results will be reported separately because they depend on provisioned development capacity.

## 19. Backpressure experiment

The standard backpressure test deliberately slows or disables a downstream dependency for **3 minutes**.

The test must demonstrate:

1. consumer throughput falls;
2. backlog/lag increases;
3. telemetry is not silently discarded;
4. downstream capacity recovers;
5. consumers drain the backlog;
6. lag returns toward normal.

Target: backlog generated by the standard slowdown should drain within **10 minutes** after recovery under the tested configuration.

Actual recovery time must be measured and reported.

## 20. Dependency-outage behavior

The project must include a controlled **3-minute downstream dependency outage**.

The implementation must document:

- retry behavior;
- retry duration/bounds;
- checkpoint behavior;
- duplicate-processing implications;
- recovery behavior;
- terminal failure behavior.

A temporary dependency outage must not cause silent telemetry loss.

## 21. Poison-message exercise

The maintenance workflow demo must include at least one command that fails processing and reaches the Service Bus DLQ.

Required demonstration:

1. command processing fails;
2. normal retries are exhausted;
3. the command appears in the DLQ;
4. the operator can inspect the reason;
5. the cause can be corrected or the command can be amended;
6. the message can be re-driven;
7. the command completes without duplicating completed work.

## 22. Observability requirements

The system must expose enough telemetry to measure at least:

- events produced/second;
- events consumed/second;
- processing success count;
- processing failure count;
- malformed-event count;
- duplicate-event count;
- late-event count;
- processing latency;
- consumer lag/backlog;
- checkpoint position/age;
- maintenance commands generated;
- Service Bus active-message count;
- Service Bus DLQ count;
- API latency;
- dependency error rate.

OpenTelemetry is the preferred instrumentation standard.

## 23. Benchmark requirements

The P10 benchmark target is:

```text
Machines:             5,000
Nominal ingress:      1,000 events/second
Late events:          2%
Duplicate events:     1%
Malformed events:     0.1%
Downstream slowdown:  3 minutes
```

The benchmark report must include:

- achieved events/second;
- achieved bytes/second;
- producer CPU and memory;
- producer errors/throttling;
- consumer throughput;
- processing latency;
- consumer lag;
- backlog recovery time;
- duplicate-handling results;
- malformed-event handling results.

If the development budget cannot support the complete target, results must be split into clearly labeled **Executed benchmark** and **Production sizing exercise** sections.

## 24. Development-cost constraint

Azure spend is an explicit non-functional requirement for this portfolio project.

Expected strategies include:

- short-lived benchmark environments;
- Terraform destroy/recreate workflows;
- scale-to-zero where supported;
- short development retention periods;
- cold storage instead of unnecessarily expensive long-term hot storage;
- local high-volume simulator testing;
- calculated production sizing kept separate from executed measurements.

The project must demonstrate engineering decisions rather than equating cloud spend with scalability.

## 25. Security baseline

From P0 onward:

- no credentials or connection strings may be committed to Git;
- local secrets must use environment variables or appropriate developer-secret mechanisms;
- CI/CD secrets must use protected secret storage;
- Terraform state must be treated as sensitive;
- production-reference administrative APIs must not be anonymously accessible.

Detailed identity, network isolation, Entra ID, and Private Link design is handled in P11.

## 26. Initial technology assumptions

| Concern | Initial direction |
| --- | --- |
| Telemetry stream | Azure Event Hubs |
| Maintenance workflow | Azure Service Bus |
| Lightweight event integration | Event Grid only where justified |
| Simulator | Python |
| Stream consumers | C#/.NET |
| Operations API | ASP.NET Core |
| Current-state store | PostgreSQL or Cosmos DB; ADR required |
| Recent telemetry | Azure Data Explorer or cost-conscious alternative; ADR required |
| Cold telemetry | Blob Storage / Data Lake |
| Application hosting | Azure Container Apps where appropriate |
| Infrastructure | Terraform |
| Observability | OpenTelemetry + Azure Monitor |

Architecture decisions with meaningful trade-offs must be documented as ADRs rather than left implicit.

## 27. Reference production-sizing scenario

This scenario is for architectural reasoning only and is not an executed benchmark requirement.

| Property | Value |
| --- | ---: |
| Sites | 20 |
| Machines/site | 1,000 |
| Machines | 20,000 |
| Reporting interval | 5 seconds |
| Average events/second | 4,000 |
| Planning event size | 350 bytes |
| Approx. payload ingress | 1.4 MB/s |
| Events/day | 345.6 million |
| Approx. raw payload/day | 121 GB |

This scenario will be used later when reasoning about partition count, Event Hubs capacity, consumer parallelism, state-store scalability, hot-storage economics, replay throughput, and network topology.

## 28. P0 exit criteria

P0 is complete when these values are reviewed and committed:

- [x] site count;
- [x] machine count;
- [x] baseline telemetry rate;
- [x] peak/test telemetry rate;
- [x] planning event size;
- [x] daily event volume;
- [x] simulator capacity target;
- [x] duplicate rate;
- [x] late-event rate;
- [x] malformed-event rate;
- [x] event ordering expectations;
- [x] delivery semantics;
- [x] late-event tolerance;
- [x] processing-latency targets;
- [x] API/query requirements;
- [x] hot-retention target;
- [x] cold-retention target;
- [x] Event Hubs retention intent;
- [x] alert requirements;
- [x] missing-data threshold;
- [x] replay requirements;
- [x] backpressure experiment;
- [x] dependency-outage exercise;
- [x] poison-message/DLQ exercise;
- [x] observability requirements;
- [x] benchmark requirements;
- [x] development-cost constraint;
- [x] executed demo workload separated from production sizing.

**P0 exit status: ready for review.**
