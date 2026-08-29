using System.Text;
using IndustriePulse.TelemetryConsumer.Processing;

namespace IndustriePulse.TelemetryConsumer.Tests.Processing;

public sealed class TelemetryEventHandlerTests
{
    [Fact]
    public async Task ProcessAsync_ValidEvent_CheckpointsAfterProcessing()
    {
        var handler = new TelemetryEventHandler();
        int checkpointCalls = 0;

        const string payload = """
        {
          "eventId": "evt-001",
          "siteId": "DE-BY-01",
          "machineId": "machine-0001"
        }
        """;

        await handler.ProcessAsync(
            Encoding.UTF8.GetBytes(payload),
            _ =>
            {
                checkpointCalls++;
                return Task.CompletedTask;
            },
            CancellationToken.None);

        Assert.Equal(1, checkpointCalls);
    }

    [Fact]
    public async Task ProcessAsync_MalformedJson_DoesNotCheckpoint()
    {
        var handler = new TelemetryEventHandler();
        int checkpointCalls = 0;

        await Assert.ThrowsAnyAsync<System.Text.Json.JsonException>(
            () => handler.ProcessAsync(
                Encoding.UTF8.GetBytes("{not-valid-json"),
                _ =>
                {
                    checkpointCalls++;
                    return Task.CompletedTask;
                },
                CancellationToken.None));

        Assert.Equal(0, checkpointCalls);
    }

    [Fact]
    public async Task ProcessAsync_MissingRequiredField_DoesNotCheckpoint()
    {
        var handler = new TelemetryEventHandler();
        int checkpointCalls = 0;

        const string payload = """
        {
          "eventId": "evt-001",
          "siteId": "DE-BY-01"
        }
        """;

        await Assert.ThrowsAsync<InvalidDataException>(
            () => handler.ProcessAsync(
                Encoding.UTF8.GetBytes(payload),
                _ =>
                {
                    checkpointCalls++;
                    return Task.CompletedTask;
                },
                CancellationToken.None));

        Assert.Equal(0, checkpointCalls);
    }

    [Fact]
    public async Task ProcessAsync_CheckpointFailure_IsPropagated()
    {
        var handler = new TelemetryEventHandler();

        const string payload = """
        {
          "eventId": "evt-001",
          "siteId": "DE-BY-01",
          "machineId": "machine-0001"
        }
        """;

        await Assert.ThrowsAsync<IOException>(
            () => handler.ProcessAsync(
                Encoding.UTF8.GetBytes(payload),
                _ => throw new IOException("Checkpoint store unavailable."),
                CancellationToken.None));
    }
}
