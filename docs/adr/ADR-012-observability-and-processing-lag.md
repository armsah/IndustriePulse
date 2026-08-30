# ADR-012: Azure Monitor observability and processing lag

- Status: Accepted
- Date: 2026-08-30
- Phase: P9

## Context

IndustriePulse needs operational visibility into the Event Hubs telemetry consumer. P9 requires Azure Monitor dashboards and, specifically, measurable processing lag.

Existing consumer metrics cover processed events, failures, checkpoints, and processing duration, but they do not show how far a consumer is behind the head of an Event Hubs partition.

The observability design must also avoid high-cardinality telemetry dimensions that would increase cost and reduce metric usability.

## Decision

The telemetry consumer exports OpenTelemetry metrics to a workspace-based Azure Application Insights resource backed by Log Analytics.

Terraform provisions:

- a Log Analytics workspace,
- a workspace-based Application Insights resource,
- an Azure Monitor Workbook named `IndustriePulse - Consumer Observability`.

The consumer exports the following metrics:

- `consumer.events.processed`
- `consumer.events.failed`
- `consumer.checkpoints`
- `consumer.processing.duration.ms`
- `consumer.processing.lag.events`
- `consumer.event.age.ms`

Metrics use only the Event Hubs partition identifier as a dimension. Machine IDs and event IDs are intentionally excluded to avoid high-cardinality metric series.

## Processing lag definition

For each processed Event Hubs event:

```text
processingLagEvents =
    max(0, lastEnqueuedSequenceNumber - currentEventSequenceNumber)

```

`lastEnqueuedSequenceNumber` is obtained from the Event Hubs partition last-enqueued-event properties.

This metric represents the consumer processing position relative to the currently observed partition head.

It is not a durable checkpoint-lag metric. After partition ownership changes, failures, or restarts, checkpoint position and currently observed processing position are related but not identical concepts.

## Event age definition

Event age is calculated from the Event Hubs broker enqueue timestamp:

```text
eventAgeMs =
    max(0, currentUtcTime - brokerEnqueuedTimeUtc)
```

This provides a wall-clock indication of how old telemetry is when it reaches application processing.

## Azure Monitor histogram semantics

OpenTelemetry histograms are exported to Application Insights as pre-aggregated custom metrics.

Workbook queries therefore use:

- `valueMax` for maximum histogram values,
- `valueMin` for minimum histogram values,
- `sum(valueSum) / sum(valueCount)` for weighted averages,
- `sum(valueSum)` for aggregated counters.

Using `avg(value)` or `max(value)` for histogram panels would incorrectly operate on pre-aggregated metric rows rather than the original measurements.

## Workbook panels

The Azure Monitor Workbook contains:

1. Processing lag
2. Event age
3. Processing outcomes
4. Processing duration

Processing lag is the primary P9 signal.

## Cost considerations

The development environment uses:

- Log Analytics `PerGB2018`,
- 30-day retention,
- a 0.5 GB daily ingestion quota,
- short-lived Azure deployments for live evidence.

This P9 deployment is a functional observability proof, not a production-capacity benchmark.

## Consequences

### Positive

- Processing backlog is directly observable.
- Catch-up behavior can be observed as lag returns toward zero.
- Event age distinguishes delayed telemetry from processing-duration problems.
- Metrics remain low cardinality.
- The dashboard is reproducible through Terraform.

### Limitations

- Processing lag is not equivalent to durable checkpoint lag.
- Application Insights metric export is aggregated rather than a raw event stream.
- P9 validates observability behavior at development scale; throughput and sustained backpressure are addressed separately in P10.
