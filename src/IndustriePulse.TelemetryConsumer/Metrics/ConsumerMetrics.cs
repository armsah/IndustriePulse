using System.Diagnostics.Metrics;

namespace IndustriePulse.TelemetryConsumer.Metrics;

public sealed class ConsumerMetrics : IDisposable
{
    public const string MeterName = "IndustriePulse.TelemetryConsumer";

    private readonly Counter<long> _processed;
    private readonly Counter<long> _failed;
    private readonly Counter<long> _checkpointed;
    private readonly Histogram<double> _processingDurationMs;
    private readonly Histogram<long> _processingLagEvents;
    private readonly Histogram<double> _eventAgeMs;

    public ConsumerMetrics()
    {
        Meter = new Meter(MeterName);

        _processed =
            Meter.CreateCounter<long>("consumer.events.processed");

        _failed =
            Meter.CreateCounter<long>("consumer.events.failed");

        _checkpointed =
            Meter.CreateCounter<long>("consumer.checkpoints");

        _processingDurationMs =
            Meter.CreateHistogram<double>(
                "consumer.processing.duration.ms",
                unit: "ms",
                description: "Telemetry event processing duration.");

        _processingLagEvents =
            Meter.CreateHistogram<long>(
                "consumer.processing.lag.events",
                unit: "{event}",
                description:
                    "Difference between the partition head sequence number and the event currently being processed.");

        _eventAgeMs =
            Meter.CreateHistogram<double>(
                "consumer.event.age.ms",
                unit: "ms",
                description:
                    "Elapsed time between Event Hubs enqueue time and consumer processing.");
    }

    public Meter Meter { get; }

    public void RecordProcessed(string partitionId) =>
        _processed.Add(
            1,
            new KeyValuePair<string, object?>(
                "partition",
                partitionId));

    public void RecordFailure(string partitionId) =>
        _failed.Add(
            1,
            new KeyValuePair<string, object?>(
                "partition",
                partitionId));

    public void RecordCheckpoint(string partitionId) =>
        _checkpointed.Add(
            1,
            new KeyValuePair<string, object?>(
                "partition",
                partitionId));

    public void RecordDuration(
        string partitionId,
        double milliseconds) =>
        _processingDurationMs.Record(
            milliseconds,
            new KeyValuePair<string, object?>(
                "partition",
                partitionId));

    public void RecordProcessingLag(
        string partitionId,
        long lagEvents) =>
        _processingLagEvents.Record(
            Math.Max(0, lagEvents),
            new KeyValuePair<string, object?>(
                "partition",
                partitionId));

    public void RecordEventAge(
        string partitionId,
        double milliseconds) =>
        _eventAgeMs.Record(
            Math.Max(0, milliseconds),
            new KeyValuePair<string, object?>(
                "partition",
                partitionId));

    public void Dispose() => Meter.Dispose();
}
