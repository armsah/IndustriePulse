# P7 Evidence: Capture, Cold Storage, and Historical Replay

## Exit criterion

**Historical batch reprocessed.**

Status: **PASS**

## Architecture validated

Live telemetry was captured from the `telemetry` Event Hub to private Azure Blob Storage using Event Hubs Capture and Avro.

Captured historical telemetry was then processed by the Python replay job and published to the isolated `telemetry-replay` Event Hub.

The `replay-processor` consumer group was used for independent downstream verification.

## Local validation

- Replay tests: 6 passed
- Simulator regression tests: 52 passed
- Terraform validation: success
- Terraform tests: 4 passed, 0 failed

## Live Azure validation

A controlled historical batch of 12 telemetry events was published to the live `telemetry` Event Hub.

Event Hubs Capture produced 8 Avro blobs.

The replay job reported:

- blobs scanned: 8
- records seen: 12
- records replayed: 12
- records rejected: 0

The dedicated replay verifier reported:

- expected events: 12
- unique event IDs: 12
- verified: true
- event IDs: `p7-history-001` through `p7-history-012`

Therefore the historical batch was successfully:

1. ingested into Event Hubs;
2. captured to durable Blob Storage;
3. read from Event Hubs Capture Avro;
4. replayed through the isolated replay Event Hub;
5. consumed and independently verified.

## Replay isolation

Historical events are replayed to `telemetry-replay`, not to the live `telemetry` Event Hub.

This prevents the P7 replay proof from implicitly updating the live Cosmos DB current-state projection or generating live maintenance commands.

## Replay semantics

The replay job preserves the original telemetry JSON payload and application-level `eventId`.

It uses `machineId` as the replay partition key.

Original Event Hubs broker sequence numbers, offsets, enqueue timestamps, and original partition identifiers are not preserved.

Replay is at-least-once. No exactly-once guarantee is claimed.

## Cost control and teardown

The Azure deployment was temporary and was destroyed after evidence collection.

- Terraform state was empty after destruction.
- The development resource group no longer existed.
- Runtime connection strings were removed from the PowerShell session.

This is a functional historical-replay proof, not a production throughput benchmark.
