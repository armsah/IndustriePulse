# IndustriePulse

Industrial telemetry and maintenance-event platform for a German manufacturing scenario.

IndustriePulse is a portfolio project focused on distributed-systems engineering using Azure, .NET, Python, and Terraform. It models factories operating CNC machines, compressors, and industrial robots that continuously emit telemetry.

The project is designed to demonstrate streaming, partitioning, consumer scaling, checkpointing, idempotency, backpressure, retries, dead-letter handling, replay, schema evolution, and observability.

## Project Status

**Current phase: P12 - Portfolio demo and documentation complete**

**All planned phases P0-P12 are complete.**

| Phase | Description                                     | Status      |
| ----- | ----------------------------------------------- | ----------- |
| P0    | Define workload and non-functional requirements | Complete    |
| P1    | Python telemetry simulator                      | Complete    |
| P2    | Azure Event Hubs infrastructure                 | Complete    |
| P3    | C# telemetry consumer and checkpointing         | Complete    |
| P4    | Machine state store and APIs                    | Complete    |
| P5    | Rule engine and maintenance alerts              | Complete    |
| P6    | DLQ and re-drive tooling                        | Complete    |
| P7    | Capture/cold storage + replay pipeline          | Complete    |
| P8    | Container Apps API/UI deployment                | Complete    |
| P9    | Observability and lag dashboards                | Complete    |
| P10   | Throughput and backpressure benchmarks          | Complete    |
| P11   | Security and private-reference design           | Complete    |
| P12   | Portfolio demo and documentation                | Complete    |

## P0 Baseline

The initial demo workload is explicitly defined as:

- **5 manufacturing sites**
- **5,000 simulated machines**
- **1 telemetry event per machine every 5 seconds**
- **~1,000 events/second nominal ingress**
- **2,000 events/second short-duration test peak**
- **350 bytes average event size for capacity planning**
- **~86.4 million telemetry events/day**
- **~30.24 GB/day raw application payload**
- **2% late/out-of-order events**
- **1% duplicate events**
- **0.1% malformed events**
- **3-minute downstream slowdown/outage exercise**
- **7 days hot telemetry retention target**
- **30 days cold telemetry retention design target**

The complete workload model and non-functional requirements are documented in [`docs/nfr.md`](docs/nfr.md).

## P1 - Telemetry Simulator

The Python simulator provides deterministic industrial telemetry generation for CNC machines, compressors, and robots.

Implemented capabilities include:

- Deterministic machine inventory and telemetry generation
- Configurable machine count and generation cycles
- Overheat and vibration-drift fault profiles
- Duplicate, late, missing, and malformed event injection
- Deterministic event IDs and reproducible fault decisions
- JSONL output for local datasets and replay
- Azure Event Hubs output
- Configurable Event Hubs partition key based on `machineId`
- Local generation and serialization benchmark tooling

A 1,000,000-event local benchmark with 10,000 virtual machines achieved approximately 10,977 events/second. This is a local simulator benchmark and is not presented as Azure or end-to-end throughput.

## P2 - Azure Event Hubs Infrastructure

Azure Event Hubs infrastructure is defined with Terraform using a reusable module under `infra/terraform/modules/event-hubs`.

The P2 configuration establishes:

- Azure Event Hubs Standard
- 8 telemetry partitions
- 1-day Event Hubs retention for the development environment
- 1 throughput unit for normal development
- `machineId` as the telemetry partition key
- Dedicated `telemetry-processor` consumer group
- Send-only producer authorization
- Terraform module tests and a standalone usage example
- Capture disabled until the replay/storage phase
- Auto-inflate disabled for predictable development cost

The infrastructure was successfully provisioned in Azure and the Python simulator completed a live smoke test by publishing 20 of 20 expected telemetry records to the `telemetry` Event Hub. This smoke test demonstrates connectivity and transport integration; it is not a production-throughput benchmark.

The development resources were destroyed after validation to minimize ongoing Azure cost.

The messaging-role, partition-key, and Event Hubs capacity decisions are documented in the Architecture Decision Records.

## P3 - C# Telemetry Consumer and Checkpointing

The telemetry consumer is implemented as a .NET 10 Worker Service using Azure Event Hubs `EventProcessorClient`.

P3 adds:

- Long-running C# Event Hubs consumption
- Dedicated listen-only consumer authorization
- Blob Storage for partition ownership and durable checkpoints
- Processing-before-checkpoint semantics
- Per-partition checkpoint blocking after a processing failure
- Graceful worker startup and shutdown
- Consumer metrics for processed events, failed events, checkpoints, and processing duration
- Automated tests covering checkpoint and failure behavior

The solution builds successfully and the P3 test suite passes **7 of 7 tests**.

Live Azure validation demonstrated:

- Successful ingestion of a clean 20-event simulator batch
- Creation of Event Hubs partition ownership and checkpoint blobs
- Clean consumer shutdown and restart
- Partition ownership reacquisition after restart
- Successful ingestion of a second 10-event batch
- Durable checkpoint timestamps advancing after restart

P3 uses correctness-first per-event checkpointing. Checkpoint batching and cadence will be evaluated during P10 throughput and backpressure testing.

A failed event prevents further checkpoint advancement for its partition during that process lifetime, avoiding the risk that later successful events move the durable checkpoint past failed work. Poison-event handling and re-drive are deferred to P6.

The short-lived Azure resources used for validation were destroyed after testing.

Detailed evidence is documented in [`docs/evidence/p3-consumer-checkpointing.md`](docs/evidence/p3-consumer-checkpointing.md).

## P4 - Machine State Store and API

P4 adds a sequence-aware current-state projection backed by Azure Cosmos DB for NoSQL and exposes it through an ASP.NET Core API.

P4 adds:

- Cosmos DB serverless infrastructure managed by Terraform
- `machineId` document identity and `/machineId` partitioning
- Repository abstraction with Cosmos and in-memory implementations
- Sequence-aware state advancement so stale or duplicate telemetry cannot regress current state
- Event Hubs consumer integration that persists state before checkpointing
- `GET /api/machines/{machineId}` current-state API
- Automated repository, consumer, API, and Terraform tests
- Short-lived end-to-end Azure validation

The full .NET test suite passes **15 of 15 tests**, and Terraform tests pass **2 of 2 runs**.

Live Azure validation demonstrated the complete path from the deterministic Python simulator through Event Hubs and the .NET consumer into Cosmos DB. A current-state API request returned sequence 2 for `CNC-00001`, confirming that the later machine state was projected and queryable.

The short-lived Azure resources used for validation were destroyed after testing.

Detailed evidence is documented in [`docs/evidence/p4-machine-state-api.md`](docs/evidence/p4-machine-state-api.md).

## P5 - Rule Engine and Maintenance Alerts

P5 adds deterministic maintenance-rule evaluation and Azure Service Bus command delivery to the telemetry processing pipeline.

Implemented capabilities:

- `OVERHEAT` rule at `temperatureC >= 85.0`;
- `HIGH_VIBRATION` rule at `vibrationMmS >= 7.0`;
- versioned `maintenance-command.v1` JSON contract;
- deterministic command IDs derived from `eventId` and `ruleId`;
- Azure Service Bus Standard `maintenance-commands` queue;
- 10-minute Service Bus duplicate-detection window;
- send-only consumer authorization and listen-only validation authorization;
- rule evaluation only when the machine-state projection advances;
- command publication before Event Hubs checkpoint advancement;
- stale/duplicate telemetry suppression;
- automated rule, serialization, consumer, and Terraform tests.

Live Azure validation exercised:

`Event Hubs -> C# consumer -> Cosmos DB -> rule engine -> Service Bus`

A deterministic 96 C telemetry event produced and validated an `OVERHEAT` maintenance command with `Critical` severity and `InspectCoolingSystem` action.

The implementation retains at-least-once semantics. Cosmos DB state advancement and Service Bus publication are not atomic; the resulting consistency gap is documented in ADR-007 as a candidate for future transactional-outbox hardening.

P5 does not claim the complete DLQ/re-drive workflow. That remains P6.

Detailed evidence is documented in [`docs/evidence/p5-rule-command-flow.md`](docs/evidence/p5-rule-command-flow.md).

## P6 - Service Bus DLQ and Re-drive

P6 adds operational tooling for inspecting and recovering maintenance-command poison messages from the Azure Service Bus dead-letter queue.

Implemented capabilities:

- .NET maintenance operations CLI;
- non-destructive DLQ inspection;
- controlled poison-message generation for reproducible validation;
- targeted message re-drive;
- deterministic replacement broker `MessageId`;
- preservation of original business identity and re-drive metadata;
- send-before-complete recovery semantics;
- dedicated Service Bus operations authorization with Send and Listen rights and no Manage right;
- automated re-drive message tests;
- operator DLQ/re-drive runbook.

The re-drive broker identity follows:

`<originalMessageId>:redrive:<deadLetterSequenceNumber>`

This allows an intentional re-drive to use a new broker identity while preserving the original business identity. It also works with the existing Service Bus duplicate-detection window to suppress a repeated recovery send during that window.

Live Azure validation exercised the complete poison-message recovery path:

`main queue -> DLQ -> inspect -> re-drive -> main queue -> consume`

The controlled poison message was dead-lettered with `InvalidMaintenanceCommand`, inspected through the CLI, re-driven as `p6-poison-001:redrive:1`, received with `redrive=True`, and completed successfully.

The final queue state contained zero active messages and zero dead-letter messages.

The workflow deliberately sends the replacement before completing the original DLQ message. It is not an atomic distributed transaction and does not claim exactly-once delivery.

The short-lived Azure resources used for P6 validation were destroyed after evidence collection, and runtime Service Bus credentials were cleared.

Detailed evidence is documented in [`docs/evidence/p6-dlq-redrive.md`](docs/evidence/p6-dlq-redrive.md).

The operational procedure is documented in [`docs/runbooks/service-bus-dlq-redrive.md`](docs/runbooks/service-bus-dlq-redrive.md).

## Planned Architecture

```text
Python Device Simulator
        |
        v
Azure Event Hubs
        |
        v
C# Stream Consumer
        |
        +------------------> Current Machine State
        |
        +------------------> Rule Engine
        |                         |
        |                         v
        |                  Azure Service Bus
        |                         |
        |                         v
        |                  Maintenance Workflow
        |
        +------------------> Hot Telemetry Store
        |
        +------------------> Blob / Data Lake
                                  |
                                  v
                             Replay Pipeline

ASP.NET Core API
        |
        v
Operations Dashboard

Observability:
OpenTelemetry + Azure Monitor
```

The exact implementation choices will be refined through [Architecture Decision Records](docs/adr/README.md) as the project progresses.

## Core Distributed-Systems Exercises

IndustriePulse will explicitly demonstrate:

- Partition-scoped ordering
- Partition-key trade-offs
- Consumer scaling relative to partition count
- Duplicate-event handling and logical idempotency
- Late and out-of-order event handling
- Checkpoint and recovery behavior
- Service Bus retries and dead-letter queues
- Poison-message re-drive
- Downstream backpressure
- Consumer lag and recovery
- Historical telemetry replay
- Schema evolution
- Dependency-outage recovery

## Technology Direction

| Area                        | Technology                     |
| --------------------------- | ------------------------------ |
| Telemetry simulation        | Python                         |
| Application services        | C# / .NET                      |
| Operations API              | ASP.NET Core                   |
| Telemetry streaming         | Azure Event Hubs               |
| Maintenance messaging       | Azure Service Bus              |
| Optional event distribution | Azure Event Grid               |
| Cold telemetry              | Azure Blob Storage / Data Lake |
| Deployment                  | Azure Container Apps           |
| Infrastructure as Code      | Terraform                      |
| Observability               | OpenTelemetry + Azure Monitor  |

State-store and hot-telemetry technologies will be selected through documented architectural decisions rather than assumed in advance.

## Repository Structure

The repository will evolve approximately toward:

```text
IndustriePulse/
|-- contracts/
|-- docs/
|   |-- adr/
|   |   `-- README.md
|   |-- benchmarks/
|   |-- demo/
|   `-- nfr.md
|-- infra/
|   `-- terraform/
|-- simulator/
|   `-- python/
|-- src/
|-- tests/
|-- tools/
|-- .gitignore
|-- LICENSE
`-- README.md
```

Directories are added only when their corresponding implementation phase begins.

## Benchmarking Policy

IndustriePulse distinguishes between:

1. **Executed benchmarks** - workloads actually run and measured.
2. **Production sizing exercises** - calculated capacity estimates based on documented assumptions.

Calculated production-scale results will not be presented as experimentally validated results.

## Documentation

- [Non-Functional Requirements and Workload Model](docs/nfr.md)
- [Architecture Decision Records](docs/adr/README.md)

Additional architecture, benchmark, replay, security, and demo documentation will be added as the corresponding implementation phases are completed.

## License

This project is licensed under the [MIT License](LICENSE).

## P7 - Capture, cold storage, and historical replay

P7 adds durable cold storage for telemetry and an isolated pipeline for reprocessing historical events.

### Architecture

```text
Live simulator
      |
      v
telemetry Event Hub
      |
      +----> live C# consumer
      |
      +----> Event Hubs Capture
                  |
                  v
          Azure Blob Storage
             Avro files
                  |
                  v
          Python replay job
                  |
                  v
       telemetry-replay Event Hub
                  |
                  v
         replay-processor group
```

### Cold-storage design

The live `telemetry` Event Hub uses native Azure Event Hubs Capture rather than a custom archival consumer.

The P7 development configuration uses:

- Azure StorageV2 with Standard LRS replication
- Cool access tier
- private `telemetry-capture` Blob container
- Avro Event Hubs Capture format
- 60-second capture interval
- 10 MiB capture size limit
- empty archives disabled

Blob Storage was selected instead of enabling ADLS Gen2 hierarchical namespace because P7 only requires durable cold storage and replay. The simpler Blob configuration keeps the portfolio deployment lower-cost and lower-complexity while leaving ADLS Gen2 as a future analytics option.

### Replay isolation

Historical telemetry is never replayed into the live `telemetry` Event Hub.

Replay uses a dedicated `telemetry-replay` Event Hub and a dedicated `replay-processor` consumer group. This isolates historical processing from the live Cosmos DB current-state projection and Service Bus maintenance-command path.

Replay authorization is also separated:

- `telemetry-replay-sender`: Send only
- `telemetry-replay-receiver`: Listen only

### Python replay tooling

The replay utility is implemented under `tools/replay/` and uses the dependencies declared in `simulator/python/pyproject.toml`.

The replay job:

1. enumerates Event Hubs Capture blobs;
2. reads Capture Avro records using `fastavro`;
3. extracts the original telemetry body;
4. validates that `machineId` is present;
5. republishes the original JSON payload to `telemetry-replay`;
6. uses `machineId` as the replay partition key;
7. annotates the broker event with replay metadata.

Invalid captured records are rejected rather than republished.

### Replay semantics

The application-level telemetry payload is preserved, including the original `eventId`.

Original Event Hubs broker metadata is not preserved. Replay creates new broker sequence numbers, offsets, enqueue timestamps, and partition metadata.

Replay is therefore explicitly **at-least-once**. Re-running a historical batch can reproduce the same application event IDs, so replay consumers must remain idempotent where side effects are involved. No exactly-once guarantee is claimed.

### Automated validation

- Replay tests: **6 passed**
- Simulator regression suite: **52 passed**
- Terraform validation: **success**
- Terraform tests: **4 passed, 0 failed**

Terraform tests cover the Event Hubs module, machine-state store, maintenance messaging, and the P7 capture/replay infrastructure contract.

### Live Azure proof

A short-lived Azure deployment was used to prove the complete historical-processing path.

A controlled batch of **12 telemetry events** was sent to the live `telemetry` Event Hub.

Event Hubs Capture produced **8 Avro blobs** across the configured Event Hub partitions.

The replay job then reported:

```json
{
  "blobsScanned": 8,
  "recordsSeen": 12,
  "recordsReplayed": 12,
  "recordsRejected": 0
}
```

A separate consumer then verified the replayed batch through the `replay-processor` consumer group:

```json
{
  "expectedCount": 12,
  "uniqueEventIds": 12,
  "verified": true
}
```

The verified application event IDs were `p7-history-001` through `p7-history-012`.

**P7 exit criterion: Historical batch reprocessed - PASS.**

### Cost control

The Azure resources used for P7 were temporary. After evidence collection:

- Terraform state was empty
- the development resource group no longer existed
- runtime connection strings were removed from the PowerShell session

The P7 live run demonstrates functional replay correctness. It is not presented as a production throughput benchmark.

### P7 documentation

- [ADR-010: Replay isolation](docs/adr/ADR-010-replay-isolation.md)
- [P7 capture/replay evidence](docs/evidence/p7-capture-replay.md)

## P8 - Azure Container Apps API/UI

P8 deploys the IndustriePulse current-state API and lightweight machine dashboard to Azure Container Apps.

### Application deployment

The existing ASP.NET Core API is packaged as a production container using a multi-stage .NET 10 Docker build.

The same application serves:

- the current machine-state API;
- a lightweight static operations dashboard;
- the `/health` platform health endpoint.

The dashboard queries:

`GET /api/machines/{machineId}`

and displays the current Cosmos DB-backed state for the requested machine.

Keeping the API and dashboard in one container limits the deployment surface for the portfolio environment while preserving the existing HTTP API boundary.

### Azure Container Apps

Terraform provisions the P8 runtime using:

- Azure Container Apps;
- external HTTPS ingress;
- target port `8080`;
- single-revision mode;
- Azure Container Registry Basic;
- `0.25` vCPU per replica;
- `0.5 GiB` memory per replica;
- minimum replicas `0`;
- maximum replicas `3`;
- liveness and readiness probes using `/health`.

The zero minimum allows the development application to scale to zero when idle. The maximum of three replicas bounds accidental development scale-out.

Scale-to-zero applies to Container Apps compute and does not imply that the complete Azure environment is free. Dependent resources such as Azure Container Registry, Event Hubs, Service Bus, Cosmos DB, Storage, monitoring, and networking can incur charges independently.

Cold-start latency after an idle scale-to-zero period is accepted for this development and portfolio workload.

### Automated validation

Final P8 validation completed successfully:

- Terraform validation: **success**
- Terraform tests: **5 passed, 0 failed**
- .NET build: **success**
- .NET tests: **26 passed, 0 failed**
- production Docker image build: **success**
- `git diff --check`: **no whitespace errors**

The Container Apps Terraform tests verify the registry SKU, revision mode, ingress configuration, target port, replica limits, CPU, and memory configuration.

### Live Azure proof

A short-lived Azure deployment was used to verify the complete P8 runtime.

The deployment demonstrated:

- successful Azure Container Apps provisioning;
- successful deployment of the `industriepulse-api:p8` image;
- healthy public HTTPS ingress;
- `/health` returning `healthy`;
- dashboard HTTP `200`;
- expected dashboard content served by ASP.NET Core;
- successful Cosmos DB-backed current-state query through the deployed API.

A deterministic machine-state document was inserted for deployment verification.

The public API returned:

```text
machineId    : P8-DEMO-CNC-0001
siteId       : SITE-P8
machineType  : CNC
temperatureC : 61.5
vibrationMmS : 2.3
sequence     : 1
```

This verified the deployed path:

```text
Browser / HTTPS client
        |
        v
Azure Container Apps ingress
        |
        v
IndustriePulse.Api
        |
        +----> Static operations dashboard
        |
        v
Cosmos DB current machine state
```

**P8 exit criterion: Container Apps API/UI deployed and scale-to-zero development economics documented - PASS.**

### Teardown and lifecycle hardening

The Azure resources used for P8 were temporary and were destroyed after evidence collection.

The initial teardown exposed an Event Hubs Capture dependency-ordering edge case. Capture storage had been removed before an Event Hub authorization-rule deletion, causing Azure to reject the operation while validating the stale Capture Blob destination.

The affected Event Hub was removed and Terraform subsequently reconciled the out-of-band deletion and completed the teardown.

Final verification confirmed:

```text
TERRAFORM_STATE_EMPTY=True
RESOURCE_GROUP_EXISTS=false
```

The Terraform dependency graph was subsequently hardened so Event Hubs resources are destroyed before their Capture storage destination.

No live P8 Azure infrastructure remained after evidence collection.

### Security boundary

P8 uses Azure Container Registry administrative credentials and a Cosmos DB connection string through Container Apps secret configuration as development simplifications.

These are not presented as the target production security model.

P11 will address managed identity, `AcrPull` role-based access, improved secret handling, and the private-network reference architecture.

### P8 documentation

- [ADR-011: Container Apps API/UI](docs/adr/ADR-011-container-apps-api-ui.md)
- [P8 Container Apps deployment evidence](docs/evidence/p8-container-apps-deployment.md)

## P9 - Azure Monitor Observability and Processing Lag

P9 adds OpenTelemetry-based consumer observability and a Terraform-managed Azure Monitor dashboard.

### Consumer metrics

The telemetry consumer exports:

- `consumer.events.processed`
- `consumer.events.failed`
- `consumer.checkpoints`
- `consumer.processing.duration.ms`
- `consumer.processing.lag.events`
- `consumer.event.age.ms`

Metrics use only the Event Hubs partition identifier as a dimension to keep metric cardinality bounded.

Processing lag is calculated from the difference between the partition last-enqueued sequence number and the sequence number currently being processed, clamped to zero.

This is a processing-position metric rather than a durable checkpoint-lag metric.

### Azure Monitor

Terraform provisions:

- a Log Analytics workspace;
- workspace-based Application Insights;
- the `IndustriePulse - Consumer Observability` Azure Monitor Workbook.

The workbook visualizes:

- processing lag;
- event age;
- processing outcomes;
- processing duration.

OpenTelemetry histogram queries use the Application Insights pre-aggregated fields `valueMin`, `valueMax`, `valueSum`, and `valueCount`.

### Live backlog evidence

A short-lived Azure deployment was used for a controlled backlog experiment.

A deterministic clean batch for 2,000 machines was published before the consumer started. Azure Monitor subsequently recorded processing lag while the consumer worked through the backlog.

Observed partition aggregates included:

- 252 samples with maximum lag of 253 events;
- 237 samples with maximum lag of 236 events.

Later metric windows recorded maximum lag values of 10, 8, and 1 events with minimum values reaching zero, demonstrating consumer catch-up.

Azure Monitor also received event-age, processed-event, checkpoint, and processing-duration metrics.

This workload is a functional observability proof rather than a production-throughput benchmark. Sustained throughput and backpressure are evaluated separately in P10.

**P9 exit criterion: processing lag measurable in Azure Monitor - PASS.**

### P9 documentation

- [ADR-012: Azure Monitor observability and processing lag](docs/adr/ADR-012-observability-and-processing-lag.md)
- [P9 observability and processing lag evidence](docs/evidence/p9-observability-lag.md)



## P10 - Throughput and Backpressure Benchmarking

P10 exercises producer throughput, controlled downstream slowdown, Event Hubs backlog growth, and recovery using explicit benchmark controls.

### Benchmark controls

The Python simulator now supports an optional target event rate and reports the actual achieved throughput instead of assuming the requested rate was reached.

The telemetry consumer supports an optional Benchmark:ProcessingDelayMs setting. The setting defaults to zero and can inject a cancellable per-event processing delay for controlled backpressure experiments.

### Executed benchmark

The Azure benchmark used:

- Azure Event Hubs Standard;
- 1 throughput unit;
- 8 telemetry partitions;
- auto-inflate disabled;
- the existing 	elemetry-processor consumer group;
- Blob-backed EventProcessorClient checkpoints;
- Cosmos DB state updates and rule evaluation in the consumer path;
- Azure Monitor metrics for processing lag and event age.

A local pacing validation targeted 100 events/second and emitted 200 events in 2.004 seconds, achieving 99.81 events/second.

The Azure producer ceiling probe requested 1,000 events/second but emitted 500 events in 33.379 seconds, achieving only 14.98 events/second. The current Python Event Hubs sink sends one event synchronously per send operation, so the publisher became the limiting component before Event Hubs capacity was approached.

This result is intentionally not presented as proof of either 1,000 events/second executed throughput or the Event Hubs service ceiling.

### Controlled backpressure

With Benchmark:ProcessingDelayMs=1000, the producer emitted 3,000 events in 176.611 seconds at 16.99 events/second while the delayed consumer processed approximately 366-416 events/minute, or about 6.1-6.9 events/second.

Because the producer arrival rate exceeded the consumer service rate, measurable backlog accumulated in Event Hubs:

- maximum captured processing lag reached 99 events on every partition;
- average lag by partition was approximately 39-49 events;
- maximum event age reached approximately 218 seconds.

### Recovery

After restoring Benchmark:ProcessingDelayMs=0, a fresh 80-event marker batch was processed across all eight partitions.

Azure Monitor showed:

- minimum lag of 0 on every partition;
- maximum lag of only 0-4 events;
- maximum marker event age of approximately 1.71 seconds.

This demonstrates that the accumulated backlog drained and normal low-lag processing resumed.

An exact uninterrupted recovery duration is not claimed because the first recovery background launcher incorrectly handled a DLL path containing spaces. The application itself was healthy, and the corrected launcher successfully completed the recovery proof.

### Limits and tradeoffs

The benchmark establishes several important boundaries:

- the current synchronous Python publisher is not suitable for measuring the Event Hubs service throughput ceiling;
- a future capacity test should use batching, asynchronous publishing, or concurrent producers;
- eight Event Hubs partitions bound useful partition-level consumer parallelism for the current topology;
- downstream processing capacity below ingress produces measurable lag and event-age growth;
- Cosmos DB writes, rules, checkpoints, and downstream dependencies contribute to consumer service time;
- auto-inflate remains disabled for benchmark repeatability and low development cost;
- the executed benchmark is an engineering demonstration rather than production capacity certification;
- the 1,000 events/second workload remains a reference sizing target rather than an executed throughput claim.

**P10 exit criterion: throughput/backpressure benchmark executed and limits/tradeoffs documented - PASS.**

### P10 documentation

- [ADR-013: Throughput and backpressure benchmark strategy](docs/adr/ADR-013-throughput-and-backpressure.md)
- [P10 throughput and backpressure benchmark evidence](docs/evidence/p10-throughput-backpressure.md)



## P11 - Security and Private-Reference Design

P11 defines the production-reference security boundary for IndustriePulse while preserving the inexpensive development deployment used by earlier phases.

### Development and production-reference separation

The development topology continues to support short-lived demonstrations using public Azure endpoints and scoped connection strings or SAS credentials.

A new `security_reference_enabled` Terraform switch defaults to `false`. When explicitly enabled, Terraform models the stronger production-reference topology without changing normal development cost.

### Identity and least privilege

The reference architecture uses separate managed identities for the API and telemetry consumer.

The API identity receives:

- `AcrPull` for container image retrieval;
- Cosmos DB Built-in Data Reader for machine-state queries.

The telemetry-consumer identity receives:

- Azure Event Hubs Data Receiver;
- Storage Blob Data Contributor for checkpoints;
- Cosmos DB Built-in Data Contributor for current-state updates;
- Azure Service Bus Data Sender for maintenance commands.

This avoids sharing broad application credentials across workloads.

### Private-reference network

The P11 Terraform reference models:

- a dedicated VNet;
- a delegated Container Apps subnet;
- a separate private-endpoint subnet;
- Event Hubs Private Link;
- Service Bus Private Link;
- Cosmos DB Private Link;
- checkpoint Blob Storage Private Link;
- telemetry capture Blob Storage Private Link;
- corresponding private DNS zones and VNet links.

Public network access and local or key authentication should be disabled only after workload identity migration and private-path validation. A private endpoint alone is not treated as sufficient isolation.

### ACR tradeoff

The development registry remains optimized for low cost. Managed identity plus `AcrPull` removes the need for registry administrative credentials in the production identity model, while stricter private registry networking remains a production option.

### Threat model and access paths

The P11 threat model covers spoofing, tampering, credential disclosure, maintenance-command abuse, checkpoint manipulation, denial of service, repudiation, and privilege escalation.

Production-reference access paths are documented for telemetry ingestion, the consumer, Blob checkpoints, Cosmos DB, Service Bus, ACR, replay, DLQ/re-drive operations, Private Link, private DNS, and Azure control-plane administration.

**P11 exit criterion: access paths documented - PASS.**

### P11 documentation

- [ADR-014: Entra identity and private connectivity reference architecture](docs/adr/ADR-014-security-and-private-connectivity.md)
- [P11 threat model](docs/security/threat-model.md)
- [P11 security access paths](docs/security/access-paths.md)



## P12 - Portfolio Demo and Documentation

P12 converts the completed engineering project into a concise, reviewer-friendly portfolio artifact.

The phase adds:

- a system-level architecture overview;
- a 10-15 minute technical demo walkthrough;
- a consolidated evidence index;
- explicit separation of measured results, sizing targets, and reference architecture claims;
- a reviewer-oriented README landing section;
- a final repository validation path that does not require continuously running Azure resources.

The demo deliberately uses captured evidence for expensive or short-lived Azure scenarios rather than requiring cloud infrastructure to remain provisioned solely for portfolio presentation.

### P12 documentation

- [Architecture overview](docs/architecture.md)
- [Portfolio demo script](docs/demo/demo-script.md)
- [Evidence index](docs/demo/evidence-index.md)

**P12 exit criterion: portfolio-ready - PASS.**

**Project status: all planned phases P0-P12 complete.**
