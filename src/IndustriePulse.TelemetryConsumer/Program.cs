using Azure.Messaging.EventHubs;
using Azure.Storage.Blobs;
using IndustriePulse.TelemetryConsumer;
using IndustriePulse.TelemetryConsumer.Configuration;
using IndustriePulse.TelemetryConsumer.Metrics;
using IndustriePulse.TelemetryConsumer.Processing;
using Microsoft.Extensions.Options;

HostApplicationBuilder builder = Host.CreateApplicationBuilder(args);

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

    return new EventProcessorClient(
        checkpointContainer,
        options.ConsumerGroup,
        options.ConnectionString);
});

builder.Services.AddHostedService<Worker>();

IHost host = builder.Build();
await host.RunAsync();

