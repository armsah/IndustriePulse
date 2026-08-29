# IndustriePulse

Industrial telemetry and maintenance-event platform for a German manufacturing scenario.

IndustriePulse is a portfolio project focused on distributed-systems engineering using Azure, .NET, Python, and Terraform. It models factories operating CNC machines, compressors, and industrial robots that continuously emit telemetry.

The project is designed to demonstrate streaming, partitioning, consumer scaling, checkpointing, idempotency, backpressure, retries, dead-letter handling, replay, schema evolution, and observability.

## Project Status

**Current phase: P4 - Machine state store and APIs complete**

| Phase | Description                                     | Status      |
| ----- | ----------------------------------------------- | ----------- |
| P0    | Define workload and non-functional requirements | Complete    |
| P1    | Python telemetry simulator                      | Complete    |
| P2    | Azure Event Hubs infrastructure                 | Complete    |
| P3    | C# telemetry consumer and checkpointing         | Complete    |
| P4    | Machine state store and APIs                    | Complete    |
| P5    | Rule engine and maintenance alerts              | Not started |
| P6    | DLQ and re-drive tooling                        | Not started |
| P7    | Cold storage and replay pipeline                | Not started |
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

1. **Executed benchmarks** GÇö workloads actually run and measured.
2. **Production sizing exercises** GÇö calculated capacity estimates based on documented assumptions.

Calculated production-scale results will not be presented as experimentally validated results.

## Documentation

* [Non-Functional Requirements and Workload Model](docs/nfr.md)
* [Architecture Decision Records](docs/adr/README.md)

Additional architecture, benchmark, replay, security, and demo documentation will be added as the corresponding implementation phases are completed.

## License

This project is licensed under the [MIT License](LICENSE).
