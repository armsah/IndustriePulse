using IndustriePulse.MachineState.Models;
using IndustriePulse.MachineState.Repositories;

namespace IndustriePulse.Api.Tests;

public sealed class MachineStateRepositoryTests
{
    [Fact]
    public async Task TryAdvanceAsync_NewMachine_StoresState()
    {
        var repository = new InMemoryMachineStateRepository();
        var state = CreateState(sequence: 1, temperatureC: 40);

        var advanced = await repository.TryAdvanceAsync(state);
        var stored = await repository.GetAsync(state.MachineId);

        Assert.True(advanced);
        Assert.NotNull(stored);
        Assert.Equal(1, stored.Sequence);
        Assert.Equal(40, stored.TemperatureC);
    }

    [Fact]
    public async Task TryAdvanceAsync_NewerSequence_AdvancesState()
    {
        var repository = new InMemoryMachineStateRepository();

        await repository.TryAdvanceAsync(
            CreateState(sequence: 10, temperatureC: 40));

        var advanced = await repository.TryAdvanceAsync(
            CreateState(sequence: 11, temperatureC: 55));

        var stored = await repository.GetAsync("machine-001");

        Assert.True(advanced);
        Assert.NotNull(stored);
        Assert.Equal(11, stored.Sequence);
        Assert.Equal(55, stored.TemperatureC);
    }

    [Fact]
    public async Task TryAdvanceAsync_OlderSequence_DoesNotRegressState()
    {
        var repository = new InMemoryMachineStateRepository();

        await repository.TryAdvanceAsync(
            CreateState(sequence: 20, temperatureC: 70));

        var advanced = await repository.TryAdvanceAsync(
            CreateState(sequence: 19, temperatureC: 30));

        var stored = await repository.GetAsync("machine-001");

        Assert.False(advanced);
        Assert.NotNull(stored);
        Assert.Equal(20, stored.Sequence);
        Assert.Equal(70, stored.TemperatureC);
    }

    [Fact]
    public async Task TryAdvanceAsync_DuplicateSequence_DoesNotRegressState()
    {
        var repository = new InMemoryMachineStateRepository();

        await repository.TryAdvanceAsync(
            CreateState(sequence: 30, temperatureC: 80));

        var advanced = await repository.TryAdvanceAsync(
            CreateState(sequence: 30, temperatureC: 20));

        var stored = await repository.GetAsync("machine-001");

        Assert.False(advanced);
        Assert.NotNull(stored);
        Assert.Equal(30, stored.Sequence);
        Assert.Equal(80, stored.TemperatureC);
    }

    private static MachineCurrentState CreateState(
        long sequence,
        double temperatureC) =>
        new()
        {
            Id = "machine-001",
            MachineId = "machine-001",
            SiteId = "site-01",
            MachineType = "cnc",
            TimestampUtc = DateTimeOffset.Parse("2026-08-29T12:00:00Z"),
            TemperatureC = temperatureC,
            VibrationMmS = 2.4,
            PressureBar = 6.2,
            Rpm = 1800,
            Sequence = sequence,
            FirmwareVersion = "1.0.0"
        };
}
