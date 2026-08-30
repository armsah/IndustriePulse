# ADR-010: Isolate Historical Telemetry Replay from the Live Pipeline

- Status: Accepted
- Phase: P7
- Date: 2026-08-30

## Context

IndustriePulse requires durable historical telemetry and a repeatable way to reprocess previously ingested events.

Azure Event Hubs retention alone is not intended to be the long-term cold-storage mechanism for the platform. Historical replay must also avoid accidentally triggering normal live side effects such as current-state projection updates or maintenance commands.

P7 therefore needs both:

1. durable capture of telemetry outside the live Event Hub; and
2. an isolated replay destination for controlled historical processing.

## Decision

Use native Azure Event Hubs Capture to archive telemetry from the live `telemetry` Event Hub into a dedicated Azure Blob Storage container.

The development configuration uses:

- Standard LRS StorageV2
- Cool access tier
- private `telemetry-capture` container
- Event Hubs Capture using Avro
- 60-second capture interval
- 10 MiB size threshold
- empty archives disabled

Historical replay is sent to a separate Event Hub named:

`telemetry-replay`

The replay Event Hub has its own consumer group:

`replay-processor`

The replay job:

1. enumerates captured Avro blobs;
2. reads Event Hubs Capture records with `fastavro`;
3. extracts the original telemetry payload from the Capture `Body`;
4. validates that the payload contains a non-empty `machineId`;
5. republishes the original payload using `machineId` as the Event Hubs partition key;
6. annotates the replayed broker event with replay metadata.

Replay credentials are separated into:

- send-only `telemetry-replay-sender`
- listen-only `telemetry-replay-receiver`

## Replay isolation

Historical telemetry is not replayed into the live `telemetry` Event Hub.

This prevents the P7 replay proof from implicitly updating the live Cosmos DB current-state projection or emitting live maintenance commands through the P5/P6 path.

Consumers intended for replay can instead attach explicitly to `telemetry-replay` using the `replay-processor` consumer group.

## Identity and ordering

The original telemetry JSON payload is preserved, including its application-level `eventId`.

The replay path also preserves the original `machineId` partition key so events for the same machine continue to map consistently to a partition.

Replay does not preserve original Event Hubs broker metadata such as:

- sequence number
- offset
- enqueue time
- original partition identifier

Those values belong to the original broker ingestion and are regenerated when the historical event is published to the replay Event Hub.

## Delivery semantics

Replay remains at-least-once.

A replay job can be run more than once, so downstream replay processors must tolerate duplicate application-level events and use the existing `eventId` identity/idempotency strategy where required.

No exactly-once guarantee is claimed.

## Storage choice

Azure Blob Storage was selected for the P7 development implementation rather than enabling Azure Data Lake Storage Gen2 hierarchical namespace.

Blob Storage satisfies the P7 cold-storage and replay requirements with less configuration and lower operational complexity for the short-lived portfolio deployment.

ADLS Gen2 remains a future option if analytics workloads require hierarchical namespace semantics.

## Consequences

Benefits:

- historical telemetry survives independently of Event Hubs retention;
- replay is explicit and operationally isolated from the live pipeline;
- the original application payload and machine partitioning semantics are retained;
- Azure-native Capture avoids introducing a custom archival consumer.

Trade-offs:

- Event Hubs Capture adds cost while enabled;
- Capture writes partitioned Avro objects rather than application-specific files;
- replay generates new broker metadata;
- replay consumers must remain duplicate tolerant;
- the current replay utility scans selected Blob prefixes or the configured container rather than maintaining a replay catalog.

## Validation

The P7 live validation deployed the stack temporarily and sent a controlled batch of 12 telemetry events.

Observed results:

- 8 Event Hubs Capture Avro blobs
- 12 captured records read
- 12 historical records replayed
- 0 rejected records
- 12 unique application event IDs consumed from `telemetry-replay`
- verifier result: `verified = true`

The Azure stack was destroyed after validation.
