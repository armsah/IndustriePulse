# IndustriePulse Evidence Index

This index separates executed engineering evidence from workload targets and reference designs.

## Phase evidence

| Phase | Engineering claim | Evidence |
| --- | --- | --- |
| P0 | Workload and NFR numbers are explicit | [NFR document](../nfr.md) |
| P1 | Deterministic local telemetry simulation and 10k-machine capability | [Simulator benchmark](../p1-simulator-benchmark.md) |
| P2 | Event Hubs infrastructure provisioned and live events published | README P2 evidence and ADR-001 through ADR-003 |
| P3 | Checkpointed Event Hubs processing survives restart | [Consumer/checkpoint evidence](../evidence/p3-consumer-checkpointing.md) |
| P4 | Current machine state can be projected and queried | [Machine-state/API evidence](../evidence/p4-machine-state-api.md) |
| P5 | Telemetry rule produces a maintenance command | [Rule/command evidence](../evidence/p5-rule-command-flow.md) |
| P6 | Poison Service Bus message can be recovered | [DLQ/re-drive evidence](../evidence/p6-dlq-redrive.md) |
| P7 | Captured historical telemetry can be reprocessed | [Capture/replay evidence](../evidence/p7-capture-replay.md) |
| P8 | API/UI runs on Azure Container Apps with development economics documented | [Container Apps evidence](../evidence/p8-container-apps-deployment.md) |
| P9 | Event processing lag is measurable through Azure Monitor | [Observability evidence](../evidence/p9-observability-lag.md) |
| P10 | Backpressure produces measurable lag and recovery is observable | [Throughput/backpressure evidence](../evidence/p10-throughput-backpressure.md) |
| P11 | Production-reference identity/private access model is defined | [Threat model](../security/threat-model.md) and [access paths](../security/access-paths.md) |
| P12 | Repository can be evaluated through a concise portfolio demo | [Demo script](demo-script.md) |

## Key measured results

| Measurement | Result | Interpretation |
| --- | ---: | --- |
| Local simulator benchmark | ~10,977 events/s | Python generation/serialization capability; not Azure throughput |
| Modeled nominal workload | ~1,000 events/s | Production sizing target; not an executed Azure result |
| Local paced producer validation | 99.81 events/s | Local pacing control behaved as configured |
| Current synchronous Azure publisher probe | 14.98 events/s | Publisher implementation became the bottleneck before Event Hubs |
| Controlled slowdown producer rate | 16.99 events/s | Arrival rate exceeded deliberately slowed consumer capacity |
| Slow consumer processing rate | ~6.1-6.9 events/s | Deliberate one-second processing delay created backlog |
| Maximum observed lag during slowdown | 99 events/partition | Backpressure was measurable |
| Maximum observed event age | ~218 seconds | Backlog translated into measurable processing age |
| Recovery marker lag | 0-4 events | Low-lag operation resumed after removing artificial slowdown |
| Recovery marker maximum age | ~1.71 seconds | Fresh events returned to low processing age |

## Claims deliberately not made

- The project does not claim that 1,000 events/second was executed end-to-end in Azure.
- The P10 publisher result is not an Event Hubs service-capacity ceiling.
- The project does not claim exactly-once processing.
- P11 does not claim that the production Private Link topology was deployed end-to-end.
- Short portfolio experiments are not presented as production capacity certification.

## Architecture decisions

The ADR collection under [`docs/adr`](../adr/README.md) records the major messaging, partitioning, checkpointing, state-store, command, replay, hosting, observability, throughput, and security decisions.

## Cost discipline

Live Azure validation resources were generally short-lived and destroyed after evidence collection. This keeps the portfolio reproducible without requiring continuously running cloud infrastructure.
