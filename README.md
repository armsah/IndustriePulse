# IndustriePulse

Industrial telemetry and maintenance-event platform for a German manufacturing scenario.

IndustriePulse is a portfolio project focused on distributed-systems engineering using Azure, .NET, Python, and Terraform. It models factories operating CNC machines, compressors, and industrial robots that continuously emit telemetry.

The project is designed to demonstrate streaming, partitioning, consumer scaling, checkpointing, idempotency, backpressure, retries, dead-letter handling, replay, schema evolution, and observability.

## Project Status

**Current phase: P7 - Capture and historical replay complete**

| Phase | Description                                     | Status      |
| ----- | ----------------------------------------------- | ----------- |
| P0    | Define workload and non-functional requirements | Complete    |
| P1    | Python telemetry simulator                      | Complete    |
| P2    | Azure Event Hubs infrastructure                 | Complete    |
| P3    | C# telemetry consumer and checkpointing         | Complete    |
| P4    | Machine state store and APIs                    | Complete    |
| P5    | Rule engine and maintenance alerts              | Complete    |
| P6    | DLQ and re-drive tooling                        | Complete    |
| P7 | Capture/cold storage + replay pipeline | Complete |
| P8    | Container Apps API/UI deployment                | Not started |
| P9    | Observability and lag dashboards                | Not started |
| P10   | Throughput and backpressure benchmarks          | Not started |
| P11   | Security and private-reference design           | Not started |
| P12   | Portfolio demo and documentation                | Not started |

## P0 Baseline

The initial demo workload is explicitly defined as:

* **5 manufacturing sites**
* **5,000 simulated machines**
* **1 telemetry event per machine every 5 seconds**
* **~1,000 events/second nominal ingress**
* **2,000 events/second short-duration test peak**
* **350 bytes average event size for capacity planning**
* **~86.4 million telemetry events/day**
* **~30.24 GB/day raw application payload**
* **2% late/out-of-order events**
* **1% duplicate events**
* **0.1% malformed events**
* **3-minute downstream slowdown/outage exercise**
* **7 days hot telemetry retention target**
* **30 days cold telemetry retention design target**

The complete workload model and non-functional requirements are documented in [`docs/nfr.md`](docs/nfr.md).

## P1 - Telemetry Simulator

The Python simulator provides deterministic industrial telemetry generation for CNC machines, compressors, and robots.

Implemented capabilities include:

* Deterministic machine inventory and telemetry generation
* Configurable machine count and generation cycles
* Overheat and vibration-drift fault profiles
* Duplicate, late, missing, and malformed event injection
* Deterministic event IDs and reproducible fault decisions
* JSONL output for local datasets and replay
* Azure Event Hubs output
* Configurable Event Hubs partition key based on `machineId`
* Local generation and serialization benchmark tooling

A 1,000,000-event local benchmark with 10,000 virtual machines achieved approximately 10,977 events/second. This is a local simulator benchmark and is not presented as Azure or end-to-end throughput.

## P2 - Azure Event Hubs Infrastructure

Azure Event Hubs infrastructure is defined with Terraform using a reusable module under `infra/terraform/modules/event-hubs`.

The P2 configuration establishes:

* Azure Event Hubs Standard
* 8 telemetry partitions
* 1-day Event Hubs retention for the development environment
* 1 throughput unit for normal development
* `machineId` as the telemetry partition key
* Dedicated `telemetry-processor` consumer group
* Send-only producer authorization
* Terraform module tests and a standalone usage example
* Capture disabled until the replay/storage phase
* Auto-inflate disabled for predictable development cost

The infrastructure was successfully provisioned in Azure and the Python simulator completed a live smoke test by publishing 20 of 20 expected telemetry records to the `telemetry` Event Hub. This smoke test demonstrates connectivity and transport integration; it is not a production-throughput benchmark.

The development resources were destroyed after validation to minimize ongoing Azure cost.

The messaging-role, partition-key, and Event Hubs capacity decisions are documented in the Architecture Decision Records.


## P3 - C# Telemetry Consumer and Checkpointing

The telemetry consumer is implemented as a .NET 10 Worker Service using Azure Event Hubs `EventProcessorClient`.

P3 adds:

* Long-running C# Event Hubs consumption
* Dedicated listen-only consumer authorization
* Blob Storage for partition ownership and durable checkpoints
* Processing-before-checkpoint semantics
* Per-partition checkpoint blocking after a processing failure
* Graceful worker startup and shutdown
* Consumer metrics for processed events, failed events, checkpoints, and processing duration
* Automated tests covering checkpoint and failure behavior

The solution builds successfully and the P3 test suite passes **7 of 7 tests**.

Live Azure validation demonstrated:

* Successful ingestion of a clean 20-event simulator batch
* Creation of Event Hubs partition ownership and checkpoint blobs
* Clean consumer shutdown and restart
* Partition ownership reacquisition after restart
* Successful ingestion of a second 10-event batch
* Durable checkpoint timestamps advancing after restart

P3 uses correctness-first per-event checkpointing. Checkpoint batching and cadence will be evaluated during P10 throughput and backpressure testing.

A failed event prevents further checkpoint advancement for its partition during that process lifetime, avoiding the risk that later successful events move the durable checkpoint past failed work. Poison-event handling and re-drive are deferred to P6.

The short-lived Azure resources used for validation were destroyed after testing.

Detailed evidence is documented in [`docs/evidence/p3-consumer-checkpointing.md`](docs/evidence/p3-consumer-checkpointing.md).
## P4 - Machine State Store and API

P4 adds a sequence-aware current-state projection backed by Azure Cosmos DB for NoSQL and exposes it through an ASP.NET Core API.

P4 adds:

* Cosmos DB serverless infrastructure managed by Terraform
* `machineId` document identity and `/machineId` partitioning
* Repository abstraction with Cosmos and in-memory implementations
* Sequence-aware state advancement so stale or duplicate telemetry cannot regress current state
* Event Hubs consumer integration that persists state before checkpointing
* `GET /api/machines/{machineId}` current-state API
* Automated repository, consumer, API, and Terraform tests
* Short-lived end-to-end Azure validation

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

- `.NET` maintenance operations CLI;
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

* Partition-scoped ordering
* Partition-key trade-offs
* Consumer scaling relative to partition count
* Duplicate-event handling and logical idempotency
* Late and out-of-order event handling
* Checkpoint and recovery behavior
* Service Bus retries and dead-letter queues
* Poison-message re-drive
* Downstream backpressure
* Consumer lag and recovery
* Historical telemetry replay
* Schema evolution
* Dependency-outage recovery

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

Directories are added only when their corresponding implementation phase begins.

## Benchmarking Policy

IndustriePulse distinguishes between:

1. **Executed benchmarks** - workloads actually run and measured.
2. **Production sizing exercises** - calculated capacity estimates based on documented assumptions.

Calculated production-scale results will not be presented as experimentally validated results.

## Documentation

* [Non-Functional Requirements and Workload Model](docs/nfr.md)
* [Architecture Decision Records](docs/adr/README.md)

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
