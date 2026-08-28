# IndustriePulse

Industrial telemetry and maintenance-event platform for a German manufacturing scenario.

IndustriePulse is a portfolio project focused on distributed-systems engineering using Azure, .NET, Python, and Terraform. It models factories operating CNC machines, compressors, and industrial robots that continuously emit telemetry.

The project is designed to demonstrate streaming, partitioning, consumer scaling, checkpointing, idempotency, backpressure, retries, dead-letter handling, replay, schema evolution, and observability.

## Project Status

**Current phase: P0 — Workload and non-functional requirements**

| Phase | Description                                     | Status        |
| ----- | ----------------------------------------------- | ------------- |
| P0    | Define workload and non-functional requirements | ✅ Complete    |
| P1    | Python telemetry simulator                      | ⬜ Not started |
| P2    | Azure Event Hubs infrastructure                 | ⬜ Not started |
| P3    | C# telemetry consumer and checkpointing         | ⬜ Not started |
| P4    | Machine state store and APIs                    | ⬜ Not started |
| P5    | Rule engine and maintenance alerts              | ⬜ Not started |
| P6    | DLQ and re-drive tooling                        | ⬜ Not started |
| P7    | Cold storage and replay pipeline                | ⬜ Not started |
| P8    | Container Apps API/UI deployment                | ⬜ Not started |
| P9    | Observability and lag dashboards                | ⬜ Not started |
| P10   | Throughput and backpressure benchmarks          | ⬜ Not started |
| P11   | Security and private-reference design           | ⬜ Not started |
| P12   | Portfolio demo and documentation                | ⬜ Not started |

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
├── contracts/
├── docs/
│   ├── adr/
│   │   └── README.md
│   ├── benchmarks/
│   ├── demo/
│   └── nfr.md
├── infrastructure/
│   └── terraform/
├── simulator/
│   └── python/
├── src/
├── tests/
├── tools/
├── .gitignore
├── LICENSE
└── README.md
```

Directories are added only when their corresponding implementation phase begins.

## Benchmarking Policy

IndustriePulse distinguishes between:

1. **Executed benchmarks** — workloads actually run and measured.
2. **Production sizing exercises** — calculated capacity estimates based on documented assumptions.

Calculated production-scale results will not be presented as experimentally validated results.

## Documentation

* [Non-Functional Requirements and Workload Model](docs/nfr.md)
* [Architecture Decision Records](docs/adr/README.md)

Additional architecture, benchmark, replay, security, and demo documentation will be added as the corresponding implementation phases are completed.

## License

This project is licensed under the [MIT License](LICENSE).
