using System.Text;
using IndustriePulse.MachineState.Models;
using IndustriePulse.MachineState.Repositories;
using IndustriePulse.TelemetryConsumer.Processing;

namespace IndustriePulse.TelemetryConsumer.Tests.Processing;

public sealed class TelemetryEventHandlerTests
{
    [Fact]
    public async Task ProcessAsync_ValidEvent_PersistsStateBeforeCheckpoint()
    {
        var repository = new InMemoryMachineStateRepository();
        var handler = new TelemetryEventHandler(repository);

        int checkpointCalls = 0;

        await handler.ProcessAsync(
            ValidPayload(sequence: 42, temperatureC: 72.5),
            _ =>
            {
                checkpointCalls++;
                return Task.CompletedTask;
            },
            CancellationToken.None);

        MachineCurrentState? state =
            await repository.GetAsync("machine-0001");

        Assert.NotNull(state);
        Assert.Equal(42, state.Sequence);
        Assert.Equal(72.5, state.TemperatureC);
        Assert.Equal(1, checkpointCalls);
    }

    [Fact]
    public async Task ProcessAsync_MalformedJson_DoesNotCheckpoint()
    {
        var repository = new InMemoryMachineStateRepository();
        var handler = new TelemetryEventHandler(repository);

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
        var repository = new InMemoryMachineStateRepository();
        var handler = new TelemetryEventHandler(repository);

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
    public async Task ProcessAsync_StateStoreFailure_DoesNotCheckpoint()
    {
        var handler =
            new TelemetryEventHandler(new FailingMachineStateRepository());

        int checkpointCalls = 0;

        await Assert.ThrowsAsync<IOException>(
            () => handler.ProcessAsync(
                ValidPayload(),
                _ =>
                {
                    checkpointCalls++;
                    return Task.CompletedTask;
                },
                CancellationToken.None));

        Assert.Equal(0, checkpointCalls);
    }

    [Fact]
    public async Task ProcessAsync_StaleEvent_DoesNotRegressState_ButCheckpoints()
    {
        var repository = new InMemoryMachineStateRepository();

        await repository.TryAdvanceAsync(
            CreateState(sequence: 50, temperatureC: 80));

        var handler = new TelemetryEventHandler(repository);

        int checkpointCalls = 0;

        await handler.ProcessAsync(
            ValidPayload(sequence: 49, temperatureC: 20),
            _ =>
            {
                checkpointCalls++;
                return Task.CompletedTask;
            },
            CancellationToken.None);

        MachineCurrentState? state =
            await repository.GetAsync("machine-0001");

        Assert.NotNull(state);
        Assert.Equal(50, state.Sequence);
        Assert.Equal(80, state.TemperatureC);
        Assert.Equal(1, checkpointCalls);
    }

    [Fact]
    public async Task ProcessAsync_CheckpointFailure_IsPropagated()
    {
        var repository = new InMemoryMachineStateRepository();
        var handler = new TelemetryEventHandler(repository);

        await Assert.ThrowsAsync<IOException>(
            () => handler.ProcessAsync(
                ValidPayload(),
                _ => throw new IOException(
                    "Checkpoint store unavailable."),
                CancellationToken.None));
    }

    private static byte[] ValidPayload(
        long sequence = 42,
        double temperatureC = 72.5)
    {
        string payload = $$"""
        {
          "eventId": "evt-001",
          "siteId": "DE-BY-01",
          "machineId": "machine-0001",
          "machineType": "cnc",
          "timestampUtc": "2026-08-29T12:00:00Z",
          "temperatureC": {{temperatureC}},
          "vibrationMmS": 3.1,
          "pressureBar": 6.5,
          "rpm": 1850,
          "sequence": {{sequence}},
          "firmwareVersion": "1.0.0"
        }
        """;

        return Encoding.UTF8.GetBytes(payload);
    }

    private static MachineCurrentState CreateState(
        long sequence,
        double temperatureC) =>
        new()
        {
            Id = "machine-0001",
            MachineId = "machine-0001",
            SiteId = "DE-BY-01",
            MachineType = "cnc",
            TimestampUtc =
                DateTimeOffset.Parse("2026-08-29T12:00:00Z"),
            TemperatureC = temperatureC,
            VibrationMmS = 3.1,
            PressureBar = 6.5,
            Rpm = 1850,
            Sequence = sequence,
            FirmwareVersion = "1.0.0"
        };

    private sealed class FailingMachineStateRepository
        : IMachineStateRepository
    {
        public Task<MachineCurrentState?> GetAsync(
            string machineId,
            CancellationToken cancellationToken = default) =>
            Task.FromResult<MachineCurrentState?>(null);

        public Task<bool> TryAdvanceAsync(
            MachineCurrentState candidate,
            CancellationToken cancellationToken = default) =>
            throw new IOException("Machine state store unavailable.");
    }
}
