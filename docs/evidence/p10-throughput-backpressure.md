# P10 Throughput and Backpressure Benchmark

Date: 2026-08-31

## Objective

Exercise Event Hubs ingestion and consumer backpressure behavior, capture an executed benchmark report, and document the measured limits and tradeoffs.

## Azure configuration

- Azure Event Hubs Standard
- 1 throughput unit
- 8 telemetry partitions
- Auto-inflate disabled
- Consumer group: telemetry-processor
- EventProcessorClient consumer with Blob checkpoints
- Cosmos DB current-state writes and rule evaluation in the processing path
- Azure Monitor / Application Insights metrics exported through OpenTelemetry

## Benchmark controls added

The Python simulator supports an optional target event rate and reports actual elapsed time and emitted events per second.

The telemetry consumer supports Benchmark:ProcessingDelayMs. A non-zero value injects a cancellable per-event delay after lag measurement and before normal event processing. The default is zero.

## Local rate-control validation

- Target: 100 events/s
- Logical events: 200
- Emitted records: 200
- Elapsed: 2.004 s
- Achieved throughput: 99.81 events/s

This validated the simulator pacing mechanism independently of Azure transport overhead.

## Azure producer ceiling probe

- Requested target: 1,000 events/s
- Logical events: 500
- Emitted records: 500
- Elapsed: 33.379 s
- Achieved throughput: 14.98 events/s

The current AzureEventHubSink performs a synchronous send for each event. The executed benchmark therefore reached the client publisher limit long before the configured Event Hubs namespace limit.

This run must not be interpreted as proof of 1,000 events/s Event Hubs throughput.

## Controlled backpressure run

The consumer was configured with Benchmark:ProcessingDelayMs=1000.

Producer result:

- Logical events: 3,000
- Emitted records: 3,000
- Elapsed: 176.611 s
- Achieved throughput: 16.99 events/s

Observed consumer throughput from Azure Monitor was approximately 366-416 processed events/minute, or about 6.1-6.9 events/s.

Because arrival rate exceeded downstream processing rate, Event Hubs retained the backlog while the consumer fell behind.

## Backpressure telemetry

Azure Monitor AppMetrics showed consumer.processing.lag.events across all eight partitions.

- Maximum lag during the controlled slowdown: 99 events on every partition in the captured slowdown interval
- Average lag by partition: approximately 39-49 events
- Maximum consumer.event.age.ms: approximately 218,023 ms
- Maximum event age: approximately 218 s, or 3.6 minutes

This demonstrates measurable lag growth while downstream processing capacity was lower than ingress.

## Recovery evidence

The artificial processing delay was removed by setting Benchmark:ProcessingDelayMs=0.

An initial background recovery launcher was invalid because the DLL path contained spaces and was not quoted correctly. The consumer application itself was healthy; a foreground launch proved successful startup. The background command was corrected by explicitly quoting the DLL argument.

After the corrected zero-delay recovery consumer was running, an 80-event marker batch was sent.

Azure Monitor then showed fresh metrics across all eight partitions:

- Total marker samples: 80
- Maximum lag by partition: 0-4 events
- Minimum lag: 0 on every partition
- Maximum observed marker event age: approximately 1,712 ms
- Minimum observed marker event age: approximately 75-94 ms

The fresh near-zero lag and sub-two-second event age demonstrate that the accumulated backlog had drained and normal processing had resumed.

An exact uninterrupted recovery duration is intentionally not reported because the earlier process-launch quoting error invalidated that timing measurement.

## Limits and tradeoffs

1. The executed test did not saturate Event Hubs. The synchronous one-event-per-send Python Azure publisher achieved only about 15-17 events/s.
2. Testing the Event Hubs service ceiling requires a batched, asynchronous, or concurrent producer.
3. Eight Event Hubs partitions bound the maximum useful partition-level consumer parallelism for this topology.
4. Artificial per-event consumer delay reliably demonstrates backpressure when downstream service rate falls below ingress.
5. Event Hubs decouples ingress from processing and retains events while the consumer is slower than the producer.
6. Cosmos DB writes, rule evaluation, checkpointing, and downstream dependencies contribute to real consumer service time.
7. Auto-inflate remained disabled to keep the benchmark configuration deterministic and low-cost.
8. The executed benchmark is a low-cost engineering demonstration, not production capacity certification.
9. The 1,000 events/s portfolio target remains a sizing target, not an executed throughput claim.
10. Recovery was demonstrated by fresh near-zero lag and low event age, but exact recovery time was not claimed because of the benchmark launcher issue.

## Exit criterion

P10 exit criterion met: throughput/backpressure behavior was executed against Azure Event Hubs, a benchmark report was captured, and the observed limits and tradeoffs are explicitly documented.
