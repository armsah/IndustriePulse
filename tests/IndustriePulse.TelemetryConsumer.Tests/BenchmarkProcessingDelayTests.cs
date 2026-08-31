using System.Diagnostics;
using IndustriePulse.TelemetryConsumer.Configuration;
using IndustriePulse.TelemetryConsumer.Processing;
using Microsoft.Extensions.Options;

namespace IndustriePulse.TelemetryConsumer.Tests;

public sealed class BenchmarkProcessingDelayTests
{
    [Fact]
    public async Task ApplyAsync_WithZeroDelay_CompletesImmediately()
    {
        var delay = CreateDelay(0);

        Task task = delay.ApplyAsync(CancellationToken.None);

        Assert.True(task.IsCompletedSuccessfully);
        await task;
    }

    [Fact]
    public async Task ApplyAsync_WithConfiguredDelay_DelaysProcessing()
    {
        var delay = CreateDelay(50);
        Stopwatch stopwatch = Stopwatch.StartNew();

        await delay.ApplyAsync(CancellationToken.None);

        stopwatch.Stop();

        Assert.True(stopwatch.ElapsedMilliseconds >= 25);
    }

    [Fact]
    public async Task ApplyAsync_WithCancellation_ObservesCancellation()
    {
        var delay = CreateDelay(10_000);
        using var cancellation = new CancellationTokenSource();
        cancellation.Cancel();

        await Assert.ThrowsAnyAsync<OperationCanceledException>(
            () => delay.ApplyAsync(cancellation.Token));
    }

    private static BenchmarkProcessingDelay CreateDelay(int milliseconds)
    {
        return new BenchmarkProcessingDelay(
            Options.Create(
                new BenchmarkOptions
                {
                    ProcessingDelayMs = milliseconds
                }));
    }
}
