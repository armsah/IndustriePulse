# P3 Evidence: C# Event Hubs Consumer and Checkpointing

## Scope

P3 implements and validates the IndustriePulse C# telemetry consumer with durable Azure Event Hubs checkpointing, explicit failure semantics, and application-level consumer metrics.

## Implementation

The consumer is a .NET 10 Worker Service using Azure Event Hubs `EventProcessorClient`.

Implemented behavior includes:

- dedicated `telemetry-processor` consumer group;
- listen-only Event Hubs consumer authorization;
- Blob-backed partition ownership and checkpoints;
- validation before checkpointing;
- no checkpoint after failed processing;
- per-partition checkpoint failure barrier;
- graceful worker startup and shutdown;
- processed-event counter;
- failed-event counter;
- checkpoint counter;
- processing-duration histogram.

The P3 metrics use `System.Diagnostics.Metrics`. Export through OpenTelemetry and Azure Monitor is intentionally deferred to P9.

## Automated Validation

The solution builds successfully with .NET 10.

The P3 test suite completed with:

- 7 tests;
- 7 succeeded;
- 0 failed;
- 0 skipped.

Tests cover successful checkpointing, malformed input, missing required fields, checkpoint failure propagation, and partition checkpoint-barrier behavior.

## Live Azure Validation

A short-lived development deployment provisioned:

- Azure Event Hubs Standard;
- 8 telemetry partitions;
- dedicated `telemetry-processor` consumer group;
- send-only producer authorization;
- listen-only consumer authorization;
- Standard LRS Storage Account;
- private Blob checkpoint container.

The Python simulator published a first clean batch of 20 expected telemetry records with no injected missing, duplicate, late, or malformed events.

Blob inspection confirmed Event Hubs processor ownership records and durable checkpoint records.

The consumer was then stopped and restarted. Partition ownership was reacquired.

A second clean batch of 10 expected telemetry records was published. Durable checkpoint timestamps advanced after the restart and second batch, demonstrating checkpoint persistence and continued progress across worker restart.

## Reliability Semantics

P3 uses at-least-once processing.

An event is checkpointed only after successful validation and processing. If processing fails, further checkpoint advancement for that partition is blocked for the lifetime of the process so that a later successful event cannot move the durable checkpoint beyond the failure.

After restart, the durable checkpoint remains before the failed work, allowing replay.

A persistent poison event can therefore block safe progress for its partition. P6 will add dead-letter and re-drive handling for that case.

Per-event checkpointing is intentionally correctness-first for P3. P10 will evaluate checkpoint batching/cadence as part of throughput and backpressure testing.

## Cost Control

The Azure resources existed only for live validation.

After validation, Terraform destroyed all 8 managed resources. Terraform state was empty afterward and the development resource group no longer existed.

Local environment variables containing Event Hubs and Storage credentials were also removed.
