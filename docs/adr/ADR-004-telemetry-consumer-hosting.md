# ADR-004: Host the telemetry consumer as a .NET Worker Service

## Status

Accepted

## Context

IndustriePulse requires a long-running telemetry consumer that reads partitioned events from Azure Event Hubs, maintains durable processing progress, exposes consumer metrics, and can later run as a containerized workload.

The consumer needs explicit control over Event Hubs partition ownership, processing lifecycle, checkpointing, shutdown behavior, and failure handling.

Azure Functions could provide an Event Hubs trigger abstraction, but the project specifically aims to demonstrate the mechanics of distributed stream processing rather than hide partition ownership and checkpoint behavior behind a trigger runtime.

## Decision

Implement the telemetry consumer as a .NET Worker Service using `EventProcessorClient` from the Azure Event Hubs SDK.

The worker:

- uses the dedicated `telemetry-processor` consumer group;
- uses Blob Storage for partition ownership and checkpoints;
- controls the processing and checkpoint boundary explicitly;
- runs locally during P3;
- is designed to move to Azure Container Apps in a later deployment phase;
- records application-level consumer metrics using `System.Diagnostics.Metrics`.

## Rationale

A Worker Service makes the Event Hubs processing lifecycle explicit and testable.

`EventProcessorClient` provides the partition load balancing, ownership, and checkpoint primitives needed for reliable at-least-once stream processing while leaving the application responsible for deciding when processing is considered successful.

This model also aligns with the planned Container Apps architecture because the same long-running worker can later be packaged and deployed without changing the core processing model.

## Consequences

### Positive

- Partition ownership and checkpoint behavior remain visible in application code.
- Processing and checkpoint ordering can be unit tested.
- The hosting model maps naturally to a containerized worker.
- The project can demonstrate failure and recovery semantics directly.
- Consumer instrumentation is independent of the final telemetry exporter.

### Negative

- The application owns more lifecycle and failure-handling logic than an Event Hubs-triggered Azure Function.
- Scaling policy must be designed explicitly in later phases.
- Operational deployment concerns are deferred until the Container Apps phase.

## Validation

P3 validated the worker against a short-lived Azure Event Hubs deployment. The worker acquired partition ownership, processed simulator telemetry, wrote Blob-backed checkpoints, shut down cleanly, restarted, reacquired ownership, and continued advancing durable checkpoints.
