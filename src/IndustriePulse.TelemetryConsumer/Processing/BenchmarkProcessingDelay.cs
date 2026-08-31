using IndustriePulse.TelemetryConsumer.Configuration;
using Microsoft.Extensions.Options;

namespace IndustriePulse.TelemetryConsumer.Processing;

public sealed class BenchmarkProcessingDelay(
    IOptions<BenchmarkOptions> options)
{
    private readonly int _processingDelayMs =
        options.Value.ProcessingDelayMs;

    public int ProcessingDelayMs => _processingDelayMs;

    public Task ApplyAsync(CancellationToken cancellationToken)
    {
        if (_processingDelayMs == 0)
        {
            return Task.CompletedTask;
        }

        return Task.Delay(
            _processingDelayMs,
            cancellationToken);
    }
}
