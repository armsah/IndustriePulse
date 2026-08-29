# ADR-005: Use Blob-backed Event Hubs checkpoints with a failure barrier

## Status

Accepted

## Context

Azure Event Hubs provides an ordered stream within each partition but does not provide exactly-once application processing.

IndustriePulse therefore needs an explicit definition of when a consumed event is safe to checkpoint.

Checkpointing an event before successful application processing can lose work. Continuing to checkpoint later events in the same partition after an earlier event fails can also move the durable checkpoint past the failed event, causing it to be skipped after restart.

The P3 consumer must preserve replayability and at-least-once processing semantics.

## Decision

Use Azure Blob Storage as the checkpoint and partition-ownership store for `EventProcessorClient`.

The processing invariant is:

1. Receive an Event Hubs event.
2. Validate and process the event.
3. Checkpoint only after successful processing.

If processing fails for an event, the consumer blocks further checkpoint advancement for that partition for the lifetime of the worker process.

Other partitions remain independently eligible to checkpoint.

After a process restart, the in-memory failure barrier is cleared, but the durable Blob checkpoint remains before the failed event. Event Hubs can therefore replay the uncheckpointed work.

The checkpoint store represents stream-processing progress only. It is not the business state store for machine state or rule-engine state.

## Rationale

This preserves the core at-least-once guarantee required by the project.

Without the partition failure barrier, event N could fail while event N+1 succeeds and advances the checkpoint. A later restart could then resume after N+1 and silently skip the failed event.

Blocking checkpoint progression on that partition prevents this loss mode while allowing unaffected partitions to continue processing.

## Consequences

### Positive

- Failed events cannot be silently skipped by later checkpoints in the same process.
- Durable checkpoints support recovery after worker restart.
- Partition failures do not globally stop unrelated partitions.
- Processing semantics are explicit and testable.

### Negative

- A permanently malformed or otherwise unprocessable event can repeatedly block safe checkpoint progression for its partition.
- P6 must introduce dead-letter and re-drive behavior for poison events.
- P3 checkpoints each successfully processed event, prioritizing correctness over maximum throughput.
- P10 must evaluate and tune checkpoint cadence or batching under load.

## Validation

Unit tests verify that valid processing checkpoints once, malformed or invalid events do not checkpoint, checkpoint failures propagate, and a blocked partition cannot checkpoint while another partition remains unaffected.

Live P3 validation used Azure Event Hubs and a private Blob checkpoint container. Checkpoint blobs were created for active partitions. After stopping and restarting the worker, partition ownership was reacquired and a second telemetry batch advanced the durable checkpoint timestamps.
