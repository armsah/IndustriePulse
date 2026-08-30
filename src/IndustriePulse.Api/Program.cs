using IndustriePulse.MachineState.Repositories;
using Microsoft.Azure.Cosmos;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddSingleton<IMachineStateRepository>(serviceProvider =>
{
    var configuration = serviceProvider.GetRequiredService<IConfiguration>();

    var connectionString =
        configuration["Cosmos:ConnectionString"]
        ?? throw new InvalidOperationException(
            "Cosmos:ConnectionString is required.");

    var databaseName =
        configuration["Cosmos:DatabaseName"] ?? "industriepulse";

    var containerName =
        configuration["Cosmos:ContainerName"] ?? "machine-state";

    var client = new CosmosClient(connectionString);
    var container = client.GetContainer(databaseName, containerName);

    return new CosmosMachineStateRepository(container);
});

var app = builder.Build();

app.UseDefaultFiles();
app.UseStaticFiles();

app.MapGet("/health", () => Results.Ok(new { status = "healthy" }))
    .WithName("Health");

app.MapGet(
    "/api/machines/{machineId}",
    async (
        string machineId,
        IMachineStateRepository repository,
        CancellationToken cancellationToken) =>
    {
        var state = await repository.GetAsync(
            machineId,
            cancellationToken);

        return state is null
            ? Results.NotFound()
            : Results.Ok(state);
    })
    .WithName("GetMachineCurrentState");

app.Run();

public partial class Program;
