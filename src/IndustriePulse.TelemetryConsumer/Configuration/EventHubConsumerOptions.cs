namespace IndustriePulse.TelemetryConsumer.Configuration;

public sealed class EventHubConsumerOptions
{
    public const string SectionName = "EventHub";

    public string ConnectionString { get; init; } = string.Empty;
    public string EventHubName { get; init; } = "telemetry";
    public string ConsumerGroup { get; init; } = "telemetry-processor";
    public string CheckpointStorageConnectionString { get; init; } = string.Empty;
    public string CheckpointContainerName { get; init; } = "eventhub-checkpoints";
}
