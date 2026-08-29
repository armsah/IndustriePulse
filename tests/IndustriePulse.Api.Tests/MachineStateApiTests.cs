using System.Net;
using System.Net.Http.Json;
using IndustriePulse.MachineState.Models;
using IndustriePulse.MachineState.Repositories;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.DependencyInjection.Extensions;

namespace IndustriePulse.Api.Tests;

public sealed class MachineStateApiTests
    : IClassFixture<MachineStateApiFactory>
{
    private readonly MachineStateApiFactory _factory;

    public MachineStateApiTests(MachineStateApiFactory factory)
    {
        _factory = factory;
    }

    [Fact]
    public async Task GetMachine_KnownMachine_ReturnsCurrentState()
    {
        const string machineId = "machine-001";

        await _factory.Repository.TryAdvanceAsync(
            new MachineCurrentState
            {
                Id = machineId,
                MachineId = machineId,
                SiteId = "site-01",
                MachineType = "cnc",
                TimestampUtc = DateTimeOffset.Parse("2026-08-29T12:00:00Z"),
                TemperatureC = 72.5,
                VibrationMmS = 3.1,
                PressureBar = 6.5,
                Rpm = 1850,
                Sequence = 42,
                FirmwareVersion = "1.0.0"
            });

        using var client = _factory.CreateClient();

        var response = await client.GetAsync(
            $"/api/machines/{machineId}");

        var state =
            await response.Content.ReadFromJsonAsync<MachineCurrentState>();

        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        Assert.NotNull(state);
        Assert.Equal(machineId, state.MachineId);
        Assert.Equal(42, state.Sequence);
        Assert.Equal(72.5, state.TemperatureC);
    }

    [Fact]
    public async Task GetMachine_UnknownMachine_Returns404()
    {
        using var client = _factory.CreateClient();

        var response = await client.GetAsync(
            "/api/machines/does-not-exist");

        Assert.Equal(HttpStatusCode.NotFound, response.StatusCode);
    }
}

public sealed class MachineStateApiFactory
    : WebApplicationFactory<Program>
{
    public InMemoryMachineStateRepository Repository { get; } = new();

    protected override void ConfigureWebHost(
        IWebHostBuilder builder)
    {
        builder.ConfigureServices(services =>
        {
            services.RemoveAll<IMachineStateRepository>();

            services.AddSingleton<IMachineStateRepository>(
                Repository);
        });
    }
}
