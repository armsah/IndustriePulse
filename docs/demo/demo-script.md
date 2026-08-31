# IndustriePulse Portfolio Demo Script

This script provides a concise reviewer walkthrough of IndustriePulse. It is designed to demonstrate the engineering decisions and captured Azure evidence without requiring permanent cloud resources.

## Demo goal

In approximately 10-15 minutes, demonstrate:

1. the workload model;
2. deterministic telemetry generation;
3. partitioned Event Hubs ingestion;
4. checkpointed .NET processing;
5. monotonic machine-state projection;
6. rule-driven maintenance commands;
7. DLQ/re-drive recovery;
8. historical capture and replay;
9. Container Apps hosting;
10. measurable processing lag and backpressure;
11. the production-reference security model.

## 1. Start with the architecture

Open [`docs/architecture.md`](../architecture.md).

Explain the primary live path:

`Python simulator -> Event Hubs -> .NET consumer -> Cosmos DB -> API`

Then show the three supporting paths:

- maintenance: `consumer -> rules -> Service Bus`;
- replay: `Event Hubs Capture -> Blob -> replay pipeline`;
- observability: `OpenTelemetry -> Application Insights -> Azure Monitor`.

Call out that `machineId` is the Event Hubs partition key and that the consumer uses Blob-backed checkpoints.

## 2. Establish the workload

Open [`docs/nfr.md`](../nfr.md).

Highlight:

- 5 sites;
- 5,000 machines;
- one event every five seconds;
- approximately 1,000 events/second nominal workload;
- 2% late events;
- 1% duplicates;
- 0.1% malformed events;
- three-minute slowdown/backpressure exercise.

State explicitly that 1,000 events/second is the modeled production workload and not an executed Azure benchmark claim.

## 3. Demonstrate deterministic simulation

From the repository root:

```powershell
Push-Location simulator\python
& .\.venv\Scripts\python.exe -m pytest
Pop-Location
```

Explain that simulator tests cover reproducibility, fault injection, event contracts, and benchmark behavior.

The captured P1 local benchmark reached approximately 10,977 events/second while modeling 10,000 virtual machines. This measures local generation and serialization, not Azure transport throughput.

Evidence: [`docs/p1-simulator-benchmark.md`](../p1-simulator-benchmark.md).

## 4. Demonstrate the .NET processing model

Run:

```powershell
dotnet build .\IndustriePulse.slnx
dotnet test .\IndustriePulse.slnx --no-build
```

Explain:

- EventProcessorClient owns partitions and persists Blob checkpoints;
- telemetry is processed before checkpoint advancement;
- machine state advances only for newer sequence numbers;
- stale and duplicate telemetry cannot regress the projection;
- rule evaluation occurs only after state advancement.

Use the P3-P5 evidence documents to show the executed Azure paths.

## 5. Demonstrate maintenance failure handling

Open:

- [`docs/evidence/p5-rule-command-flow.md`](../evidence/p5-rule-command-flow.md);
- [`docs/evidence/p6-dlq-redrive.md`](../evidence/p6-dlq-redrive.md);
- [`docs/runbooks/service-bus-dlq-redrive.md`](../runbooks/service-bus-dlq-redrive.md).

Explain the sequence:

`telemetry -> state advance -> rule -> maintenance command -> Service Bus`

Then explain how a poison message reaches the DLQ, is inspected, and is explicitly re-driven using the operations tooling.

## 6. Demonstrate historical replay

Open [`docs/evidence/p7-capture-replay.md`](../evidence/p7-capture-replay.md).

Explain that Event Hubs Capture writes Avro data to Blob Storage and the Python replay pipeline republishes historical records through an isolated replay Event Hub/consumer group.

Isolation prevents historical reprocessing from silently interfering with the live consumer checkpoint path.

## 7. Show the hosted API/UI

Open [`docs/evidence/p8-container-apps-deployment.md`](../evidence/p8-container-apps-deployment.md).

Explain:

- ASP.NET Core API/UI containerization;
- Azure Container Registry image delivery;
- Azure Container Apps Consumption hosting;
- external HTTPS ingress for the portfolio demo;
- scale-to-zero / low-cost development economics.

The live deployment was short-lived and destroyed after evidence collection.

## 8. Show observability

Open [`docs/evidence/p9-observability-lag.md`](../evidence/p9-observability-lag.md).

Show that OpenTelemetry instrumentation records:

- processing lag;
- event age;
- processing outcomes;
- processing duration;
- checkpoint behavior.

Explain that Azure Monitor recorded backlog growth and later consumer catch-up.

## 9. Show backpressure rather than claiming synthetic scale

Open [`docs/evidence/p10-throughput-backpressure.md`](../evidence/p10-throughput-backpressure.md).

Highlight the controlled slowdown:

- producer: 16.99 events/second;
- slowed consumer: approximately 6.1-6.9 events/second;
- maximum lag: 99 events on each partition;
- maximum event age: approximately 218 seconds.

Then highlight recovery:

- fresh marker lag: 0-4 events;
- fresh marker maximum event age: approximately 1.71 seconds.

Also call out the negative benchmark result: the current synchronous Python Azure publisher reached only 14.98 events/second during the ceiling probe. That is an application publisher limitation, not an Event Hubs capacity measurement.

This distinction is intentional: the project separates measured results from mathematical production sizing.

## 10. Show production-reference security

Open:

- [`docs/security/threat-model.md`](../security/threat-model.md);
- [`docs/security/access-paths.md`](../security/access-paths.md);
- [`docs/adr/ADR-014-security-and-private-connectivity.md`](../adr/ADR-014-security-and-private-connectivity.md).

Explain the intended production migration:

`connection strings / SAS -> Entra workload identity -> least-privilege RBAC`

and:

`public data-plane endpoints -> VNet integration + Private Link + private DNS`

Clarify that P11 is a validated production-reference design and not an executed claim that all private paths were deployed.

## 11. Validate the repository

Run the complete local validation suite:

```powershell
Push-Location simulator\python
& .\.venv\Scripts\python.exe -m pytest
Pop-Location

dotnet build .\IndustriePulse.slnx
dotnet test .\IndustriePulse.slnx --no-build

Push-Location infra\terraform
terraform fmt -check -recursive
terraform validate
terraform test
Pop-Location
```

This verifies the simulator, .NET solution, and Terraform reference architecture without provisioning Azure resources.

## 12. Close with engineering tradeoffs

The main discussion points for a technical interview are:

- Event Hubs partition count bounds partition-level parallelism;
- per-event checkpointing favors correctness over maximum throughput;
- Cosmos state advancement and Service Bus publication are not atomic;
- at-least-once delivery requires idempotency throughout the pipeline;
- replay is deliberately isolated from the live path;
- the existing Python Azure sink is synchronous and should be batched/concurrent for a real service-capacity benchmark;
- production security should migrate from shared secrets to managed/workload identities and private data paths;
- short-lived Azure validation keeps portfolio operating cost low.

## Evidence index

For a single entry point to all executed evidence and reference-design material, see [`docs/demo/evidence-index.md`](evidence-index.md).
