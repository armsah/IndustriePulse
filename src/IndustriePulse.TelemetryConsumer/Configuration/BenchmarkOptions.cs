namespace IndustriePulse.TelemetryConsumer.Configuration;

public sealed class BenchmarkOptions
{
    public const string SectionName = "Benchmark";

    public int ProcessingDelayMs { get; init; }
}
