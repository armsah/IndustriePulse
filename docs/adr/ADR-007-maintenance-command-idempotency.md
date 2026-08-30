# ADR-007: Maintenance command idempotency and duplicate-processing strategy

- **Status:** Accepted
- **Phase:** P5
- **Date:** 2026-08-30

## Context

IndustriePulse processes telemetry from Azure Event Hubs using an at-least-once consumer. Event Hubs delivery, worker restarts, checkpoint failures, and retries can cause the same logical telemetry event to be processed more than once.

P5 introduces maintenance rules that translate qualifying telemetry into Azure Service Bus commands. Duplicate telemetry processing must therefore not create uncontrolled duplicate maintenance actions.

The current machine-state projection already rejects stale or duplicate telemetry when the incoming `sequence` is not newer than the stored state.

## Decision

Maintenance rules are evaluated only when the current machine-state projection successfully advances.

Two deterministic threshold rules are implemented:

- `OVERHEAT`: `temperatureC >= 85.0`
- `HIGH_VIBRATION`: `vibrationMmS >= 7.0`

Each emitted maintenance command has a deterministic identity derived from the triggering telemetry event and rule:

`commandId = SHA256(eventId + ":" + ruleId)`

The Service Bus message `MessageId` is set to the same `commandId`.

The P5 Service Bus queue enables duplicate detection with a 10-minute history window. This provides an additional broker-side duplicate suppression mechanism for repeated sends using the same `MessageId`.

The maintenance command schema is versioned as `1.0` and is stored in:

`contracts/maintenance-command.v1.json`

The telemetry consumer uses a send-only Service Bus authorization rule. Validation uses a separate listen-only authorization rule.

## Processing boundary

For a telemetry event that advances machine state, processing is:

1. Validate telemetry.
2. Advance the machine current-state projection.
3. Evaluate maintenance rules.
4. Publish any resulting maintenance commands.
5. Advance the Event Hubs checkpoint.

A stale or duplicate telemetry event is considered successfully processed and may be checkpointed, but it does not produce another maintenance command.

If command publication fails, the Event Hubs checkpoint is not advanced.

## Consequences

The design prevents stale or duplicate telemetry from repeatedly triggering maintenance rules during normal processing and gives commands stable identities across retries.

Service Bus duplicate detection further suppresses duplicate sends that use the same `MessageId` within the configured history window.

The solution remains explicitly at-least-once. It does not claim exactly-once delivery.

## Known consistency limitation

The Cosmos DB machine-state update and Service Bus send are not part of one atomic transaction.

Machine state currently advances before command publication. If the state write succeeds but Service Bus publication fails, Event Hubs does not checkpoint the event. On redelivery, however, the state repository can classify that event as stale because its sequence was already persisted, which can suppress regeneration of the maintenance command.

Therefore P5 does not provide transactional atomicity between the state projection and maintenance-command publication.

A transactional-outbox or equivalent durable command-intent pattern is a future hardening option.

## P6 boundary

P5 configures Service Bus delivery and dead-letter-related queue settings, but does not claim a complete poison-message, DLQ inspection, or re-drive workflow.

Those behaviors belong to P6 and ADR-009.
