# P9 Evidence: Azure Monitor observability and processing lag

Date: 2026-08-30

## Objective

Demonstrate the P9 exit criterion:

> Processing lag measurable.

The test also verifies that the telemetry consumer exports operational metrics into Azure Monitor and that the Terraform-managed workbook can visualize those metrics.

## Azure observability deployment

Terraform provisioned:

- Log Analytics workspace
- workspace-based Application Insights
- Azure Monitor Workbook: `IndustriePulse - Consumer Observability`

The workbook includes panels for:

- processing lag,
- event age,
- processing outcomes,
- processing duration.

The final workbook queries use Application Insights pre-aggregated metric fields:

- `valueMax`
- `valueMin`
- `valueSum`
- `valueCount`

## Controlled backlog experiment

A deterministic telemetry batch was generated before starting the consumer.

Test workload:

- 2,000 machines
- 1 telemetry cycle
- deterministic seed
- late-event rate: 0
- duplicate rate: 0
- malformed rate: 0
- missing-event rate: 0

The consumer was started after the events had already been published, creating a controlled backlog.

This experiment is a functional observability test. It is not presented as the project production-scale throughput benchmark.

## Observed Azure Monitor metrics

Application Insights received:

- `consumer.events.processed`
- `consumer.checkpoints`
- `consumer.processing.duration.ms`
- `consumer.processing.lag.events`
- `consumer.event.age.ms`

Metric dimensions were limited to the Event Hubs partition identifier.

## Processing lag evidence

Azure Monitor showed substantial processing lag while the consumer was working through the backlog.

Observed examples included partition aggregates with:

- 252 samples and a maximum lag of 253 events,
- 237 samples and a maximum lag of 236 events.

Later metric windows showed much smaller lag values, including:

- maximum 10 events with minimum 0,
- maximum 8 events with minimum 0,
- maximum 1 event with minimum 0.

The combination of positive maximum lag and subsequent zero minimum values demonstrates both measurable backlog and consumer catch-up.

## Event age evidence

`consumer.event.age.ms` was also present in Azure Monitor.

During the controlled backlog, observed event-age aggregates were roughly in the 90 to 160 second range, confirming that broker enqueue time can be used to measure telemetry staleness at processing time.

## Processing outcomes and duration

Azure Monitor also contained:

- processed-event counters,
- checkpoint counters,
- processing-duration histograms.

This verifies that the workbook can correlate backlog with consumer processing activity.

## Workbook correction

The initial workbook queries treated OpenTelemetry histogram rows as raw scalar samples.

The workbook was corrected to use Application Insights aggregation semantics:

- maximum: `max(valueMax)`
- minimum: `min(valueMin)`
- average: `sum(valueSum) / sum(valueCount)`
- counters: `sum(valueSum)`

Terraform planned the workbook correction as:

```text
0 to add, 1 to change, 0 to destroy
```

The live Terraform state was subsequently verified to contain the corrected KQL.

## Deployment notes

The broader development stack had two setup issues unrelated to the P9 observability implementation:

1. the previously used P8 Container Apps image was not present after recreating the development ACR;
2. Event Hubs Capture encountered a transient destination/authentication-propagation issue.

The P9 Azure Monitor resources were successfully provisioned. The required Event Hubs consumer authorization rule was recovered with a targeted Terraform apply.

These targeted operations were recovery actions, not the normal deployment workflow.

## Exit criterion

P9 exit criterion: **met**.

Processing lag was measured in live Azure Monitor telemetry, rose while backlog existed, and returned toward zero as the consumer caught up.
