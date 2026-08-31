using Azure.Messaging.EventHubs;
using Azure.Messaging.ServiceBus;
using Azure.Storage.Blobs;
using IndustriePulse.MachineState.Repositories;
using IndustriePulse.Maintenance.Messaging;
using IndustriePulse.Maintenance.Rules;
using IndustriePulse.TelemetryConsumer;
using IndustriePulse.TelemetryConsumer.Configuration;
using IndustriePulse.TelemetryConsumer.Metrics;
using IndustriePulse.TelemetryConsumer.Processing;
using Microsoft.Azure.Cosmos;
using Microsoft.Extensions.Options;
using Azure.Monitor.OpenTelemetry.Exporter;
using OpenTelemetry.Metrics;

HostApplicationBuilder builder = Host.CreateApplicationBuilder(args);

string? applicationInsightsConnectionString =
    builder.Configuration[
        "ApplicationInsights:ConnectionString"];

if (!string.IsNullOrWhiteSpace(
        applicationInsightsConnectionString))
{
    builder.Services
        .AddOpenTelemetry()
        .WithMetrics(metrics =>
        {
            metrics
                .AddMeter(ConsumerMetrics.MeterName)
                .AddAzureMonitorMetricExporter(options =>
                {
                    options.ConnectionString =
                        applicationInsightsConnectionString;
                });
        });
}

builder.Services
    .AddOptions<EventHubConsumerOptions>()
    .Bind(builder.Configuration.GetSection(EventHubConsumerOptions.SectionName))
    .Validate(
        options => !string.IsNullOrWhiteSpace(options.ConnectionString),
        "EventHub:ConnectionString is required.")
    .Validate(
        options => !string.IsNullOrWhiteSpace(options.EventHubName),
        "EventHub:EventHubName is required.")
    .Validate(
        options => !string.IsNullOrWhiteSpace(options.ConsumerGroup),
        "EventHub:ConsumerGroup is required.")
    .Validate(
        options => !string.IsNullOrWhiteSpace(options.CheckpointStorageConnectionString),
        "EventHub:CheckpointStorageConnectionString is required.")
    .Validate(
        options => !string.IsNullOrWhiteSpace(options.CheckpointContainerName),
        "EventHub:CheckpointContainerName is required.")
    .ValidateOnStart();

builder.Services
    .AddOptions<BenchmarkOptions>()
    .Bind(builder.Configuration.GetSection(BenchmarkOptions.SectionName))
    .Validate(
        options => options.ProcessingDelayMs >= 0,
        "Benchmark:ProcessingDelayMs must be greater than or equal to zero.")
    .ValidateOnStart();

builder.Services.AddSingleton<BenchmarkProcessingDelay>();

builder.Services.AddSingleton<IMachineStateRepository>(sp =>
{
    IConfiguration configuration =
        sp.GetRequiredService<IConfiguration>();

    string connectionString =
        configuration["Cosmos:ConnectionString"]
        ?? throw new InvalidOperationException(
            "Cosmos:ConnectionString is required.");

    string databaseName =
        configuration["Cosmos:DatabaseName"]
        ?? "industriepulse";

    string containerName =
        configuration["Cosmos:ContainerName"]
        ?? "machine-state";

    var client = new CosmosClient(connectionString);

    return new CosmosMachineStateRepository(
        client.GetContainer(databaseName, containerName));
});

// P5 maintenance rule engine.
builder.Services.AddSingleton<IMaintenanceRuleEngine,
    ThresholdMaintenanceRuleEngine>();

// P5 Service Bus client.
// The runtime connection string should use a send-only authorization rule.
builder.Services.AddSingleton(sp =>
{
    IConfiguration configuration =
        sp.GetRequiredService<IConfiguration>();

    string connectionString =
        configuration["ServiceBus:ConnectionString"]
        ?? throw new InvalidOperationException(
            "ServiceBus:ConnectionString is required.");

    return new ServiceBusClient(connectionString);
});

// One sender is reused for the lifetime of the worker.
builder.Services.AddSingleton(sp =>
{
    IConfiguration configuration =
        sp.GetRequiredService<IConfiguration>();

    string queueName =
        configuration["ServiceBus:QueueName"]
        ?? "maintenance-commands";

    ServiceBusClient client =
        sp.GetRequiredService<ServiceBusClient>();

    return client.CreateSender(queueName);
});

builder.Services.AddSingleton<IMaintenanceCommandPublisher,
    ServiceBusMaintenanceCommandPublisher>();

builder.Services.AddSingleton<TelemetryEventHandler>();
builder.Services.AddSingleton<PartitionCheckpointGate>();
builder.Services.AddSingleton<ConsumerMetrics>();

builder.Services.AddSingleton(sp =>
{
    EventHubConsumerOptions options =
        sp.GetRequiredService<IOptions<EventHubConsumerOptions>>().Value;

    var checkpointContainer = new BlobContainerClient(
        options.CheckpointStorageConnectionString,
        options.CheckpointContainerName);

    var processorOptions =
        new EventProcessorClientOptions
        {
            TrackLastEnqueuedEventProperties = true
        };

    return new EventProcessorClient(
        checkpointContainer,
        options.ConsumerGroup,
        options.ConnectionString,
        processorOptions);
});

builder.Services.AddHostedService<Worker>();

IHost host = builder.Build();
await host.RunAsync();
