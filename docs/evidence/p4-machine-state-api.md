# P4 Evidence - Machine State Store and API

## Objective

P4 adds a durable current-state projection for machines and exposes that state through an ASP.NET Core API.

Acceptance criteria:

- PostgreSQL/Cosmos decision documented
- Machine state store implemented
- API tests implemented
- Current-state query demonstrated end to end

## Storage Decision

ADR-006 selects Azure Cosmos DB for NoSQL for the current machine-state projection.

The projection uses:

- document identity: `machineId`
- partition key: `/machineId`
- consistency: Session
- development deployment mode: serverless
- database: `industriepulse`
- container: `machine-state`

The primary access pattern is a point read for the latest known state of one machine.

State is sequence-aware. A candidate event advances stored state only when its `sequence` is greater than the currently stored sequence. Duplicate, late, and out-of-order events therefore cannot regress current machine state.

## Consumer Integration

The Event Hubs consumer now projects validated telemetry through `IMachineStateRepository`.

Processing order:

1. Parse and validate telemetry.
2. Attempt to advance current machine state.
3. Checkpoint the Event Hubs event only after state processing succeeds.

A stale or duplicate event is successfully processed and may be checkpointed, but it does not replace newer machine state.

Malformed telemetry or a state-store failure does not checkpoint the event. The existing partition checkpoint gate prevents later successful events in the partition from moving the durable checkpoint past the failure during that process lifetime.

## API

The ASP.NET Core API exposes `GET /api/machines/{machineId}`.

- `200 OK` returns current machine state when the machine exists.
- `404 Not Found` is returned when the machine does not exist.

## Automated Validation

The .NET test suite completed successfully:

```text
Test summary: total: 15, failed: 0, succeeded: 15, skipped: 0
```

Tests cover repository state advancement, stale and duplicate handling, API success and 404 behavior, consumer persistence before checkpointing, validation failures, state-store failures, checkpoint failures, and partition checkpoint-gate behavior.

Terraform validation completed successfully.

```text
Success! 2 passed, 0 failed.
```

Terraform tests cover the Event Hubs module and the P4 Cosmos configuration, including serverless capability, Session consistency, database and container names, `/machineId` partitioning, and partition-key version 2.

## Live Azure Validation

A short-lived Azure environment was provisioned with Terraform.

```text
Apply complete! Resources: 11 added, 0 changed, 0 destroyed.
```

The live path was:

```text
Python simulator
      |
      v
Azure Event Hubs
      |
      v
.NET telemetry consumer
      |
      v
Azure Cosmos DB
      |
      v
ASP.NET Core API
```

A live request to `GET /api/machines/CNC-00001` returned current state with `sequence` equal to 2 and timestamp `2026-01-01T00:00:05+00:00`.

The sequence value demonstrates that the later event from the two-cycle telemetry run became the current projected state.

## Cleanup

The short-lived Azure environment was destroyed immediately after validation.

Post-destroy verification confirmed:

- `terraform state list` returned no resources.
- the Azure resource group no longer existed.
- Event Hubs, checkpoint-storage, Cosmos, and producer runtime credentials were removed from the PowerShell environment.

No Azure infrastructure remains deployed after the P4 validation.
