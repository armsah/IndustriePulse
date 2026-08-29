# ADR-006: Machine Current-State Store

## Status

Accepted

## Context

IndustriePulse requires a durable current-state projection for each simulated machine.

The telemetry stream is append-oriented and contains duplicate, late, and out-of-order records. The current-state store serves a different access pattern: retrieve the latest known state for a specific machine with low latency.

The initial workload contains approximately 5,000 machines, with a production-sizing exercise extending beyond that baseline.

P4 requires:

- Durable current machine state
- Efficient lookup by machine ID
- Safe handling of duplicate and out-of-order telemetry
- A repository abstraction usable by both processing and API code
- Low-cost development and short-lived Azure validation
- Straightforward horizontal scaling

PostgreSQL and Azure Cosmos DB for NoSQL were evaluated.

## PostgreSQL

Advantages:

- Strong relational model and transactional semantics
- Familiar SQL querying
- Mature indexing and tooling
- Appropriate if current state develops significant relational requirements

Disadvantages for this projection:

- The primary access pattern does not require joins or relational traversal
- The machine-state document maps naturally to a key-value/document model
- Azure-hosted PostgreSQL requires provisioned database resources while running
- Relational capabilities would add complexity that P4 does not currently need

## Azure Cosmos DB for NoSQL

Advantages:

- Natural document representation for machine current state
- Efficient point reads when both item ID and partition key are known
- Horizontal partitioning is built into the service
- Serverless capacity is appropriate for low-volume development and short-lived portfolio validation
- Fits the expected access pattern of one current-state document per machine

Disadvantages:

- Request-unit consumption must be understood and monitored
- Cross-partition queries can be more expensive than point reads
- Relational joins and constraints are not the design center
- Application-level concurrency and ordering rules remain necessary

## Decision

Use Azure Cosmos DB for NoSQL for the P4 machine current-state projection.

Each machine has one current-state document.

The logical identity is:

- `id`: machine ID
- partition key: `/machineId`

The API should use point reads whenever querying a machine by ID.

The state projection stores the telemetry sequence number and timestamp alongside the latest measurements.

A telemetry event may advance current state only when its sequence is newer than the sequence already stored for that machine.

Duplicate or stale telemetry must not regress current state.

The storage implementation will be accessed through an application-level repository abstraction so domain/application logic does not depend directly on the Cosmos SDK.

## Consequences

The current-state data model is optimized for machine lookup rather than historical telemetry analysis.

Historical telemetry remains a separate concern and will be addressed by the hot/cold telemetry phases.

The repository abstraction allows unit and API tests to run without requiring Azure Cosmos DB.

P4 will use short-lived Azure infrastructure only for live integration evidence and will destroy it after validation.

Production partitioning, RU consumption, and scaling observations will be revisited during throughput and backpressure testing.
