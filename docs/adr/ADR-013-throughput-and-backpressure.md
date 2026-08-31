# ADR-013: Throughput and Backpressure Benchmark Strategy

## Status

Accepted

## Context

IndustriePulse requires an honest demonstration of throughput, downstream slowdown, Event Hubs backlog growth, and recovery without presenting mathematical production sizing as executed scale.

The existing Python Azure publisher sends one event synchronously per Event Hubs send operation. That implementation is suitable for functional testing but is not a high-throughput load generator.

## Decision

Add explicit benchmark controls rather than changing the normal processing semantics:

- Add optional producer pacing through target-events-per-second.
- Always report achieved throughput rather than assuming the requested rate was reached.
- Add Benchmark:ProcessingDelayMs to the telemetry consumer.
- Keep the default processing delay at zero.
- Inject the benchmark delay before durable event processing so downstream capacity can be reduced deterministically.
- Use Azure Monitor consumer lag and event age as the primary backpressure evidence.
- Keep Event Hubs Standard at 1 throughput unit with eight partitions and auto-inflate disabled during the low-cost benchmark.

## Consequences

The benchmark can reproducibly force arrival rate above consumer service rate and demonstrate Event Hubs backlog behavior.

The synchronous Python publisher currently limits executed Azure ingestion to approximately 15-17 events/s in this environment. Therefore the benchmark does not establish the Event Hubs service throughput ceiling.

A future service-capacity benchmark should use producer batching, asynchronous publishing, or multiple concurrent producers.

The benchmark delay is explicitly configuration-controlled and disabled by default, so normal consumer behavior is unchanged.

Exact backlog recovery timing should only be reported when the complete benchmark harness runs uninterrupted. During P10, a process-launch quoting error interrupted the first recovery measurement, so only successful eventual recovery is claimed.

## Alternatives considered

### Increase Event Hubs throughput units

Rejected for this benchmark because the producer was already the limiting component and additional throughput units would add cost without improving the executed test.

### Enable auto-inflate

Rejected for the benchmark because it would reduce configuration determinism and could increase cost while not addressing the publisher bottleneck.

### Claim the requested producer rate

Rejected. IndustriePulse records achieved throughput and distinguishes executed results from reference production sizing.

## Result

P10 demonstrates measurable backlog growth when downstream capacity is constrained and near-zero lag after normal processing capacity is restored, while explicitly documenting the publisher bottleneck and other capacity tradeoffs.
