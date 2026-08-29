using System.Diagnostics.Metrics;

namespace IndustriePulse.TelemetryConsumer.Metrics;

public sealed class ConsumerMetrics
{
    public const string MeterName = "IndustriePulse.TelemetryConsumer";

    private readonly Counter<long> _processed;
    private readonly Counter<long> _failed;
    private readonly Counter<long> _checkpointed;
    private readonly Histogram<double> _processingDurationMs;

    public ConsumerMetrics()
    {
        Meter = new Meter(MeterName);

        _processed = Meter.CreateCounter<long>("consumer.events.processed");
        _failed = Meter.CreateCounter<long>("consumer.events.failed");
        _checkpointed = Meter.CreateCounter<long>("consumer.checkpoints");
        _processingDurationMs =
            Meter.CreateHistogram<double>("consumer.processing.duration.ms");
    }

    public Meter Meter { get; }

    public void RecordProcessed(string partitionId) =>
        _processed.Add(1, new KeyValuePair<string, object?>("partition", partitionId));

    public void RecordFailure(string partitionId) =>
        _failed.Add(1, new KeyValuePair<string, object?>("partition", partitionId));

    public void RecordCheckpoint(string partitionId) =>
        _checkpointed.Add(1, new KeyValuePair<string, object?>("partition", partitionId));

    public void RecordDuration(string partitionId, double milliseconds) =>
        _processingDurationMs.Record(
            milliseconds,
            new KeyValuePair<string, object?>("partition", partitionId));
}
