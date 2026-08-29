using System.Diagnostics;
using Azure.Messaging.EventHubs;
using Azure.Messaging.EventHubs.Processor;
using IndustriePulse.TelemetryConsumer.Metrics;
using IndustriePulse.TelemetryConsumer.Processing;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;

namespace IndustriePulse.TelemetryConsumer;

public sealed class Worker(
    EventProcessorClient processor,
    TelemetryEventHandler handler,
    PartitionCheckpointGate checkpointGate,
    ConsumerMetrics metrics,
    ILogger<Worker> logger) : BackgroundService
{
    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        processor.ProcessEventAsync += ProcessEventAsync;
        processor.ProcessErrorAsync += ProcessErrorAsync;

        logger.LogInformation("Starting Event Hubs telemetry consumer.");

        try
        {
            await processor.StartProcessingAsync(stoppingToken);
            await Task.Delay(Timeout.Infinite, stoppingToken);
        }
        catch (OperationCanceledException) when (stoppingToken.IsCancellationRequested)
        {
            logger.LogInformation("Telemetry consumer shutdown requested.");
        }
        finally
        {
            if (processor.IsRunning)
            {
                await processor.StopProcessingAsync(CancellationToken.None);
            }

            processor.ProcessEventAsync -= ProcessEventAsync;
            processor.ProcessErrorAsync -= ProcessErrorAsync;
        }
    }

    private async Task ProcessEventAsync(ProcessEventArgs args)
    {
        Stopwatch stopwatch = Stopwatch.StartNew();
        string partitionId = args.Partition.PartitionId;
        bool checkpointed = false;

        try
        {
            await handler.ProcessAsync(
                args.Data.EventBody.ToMemory(),
                async cancellationToken =>
                {
                    if (!checkpointGate.CanCheckpoint(partitionId))
                    {
                        return;
                    }

                    await args.UpdateCheckpointAsync(cancellationToken);
                    checkpointed = true;
                },
                args.CancellationToken);

            metrics.RecordProcessed(partitionId);

            if (checkpointed)
            {
                metrics.RecordCheckpoint(partitionId);
            }
        }
        catch (OperationCanceledException) when (args.CancellationToken.IsCancellationRequested)
        {
            throw;
        }
        catch (Exception ex)
        {
            checkpointGate.Block(partitionId);
            metrics.RecordFailure(partitionId);

            logger.LogError(
                ex,
                "Failed processing Event Hubs event from partition {PartitionId}. Further checkpoints for this partition are blocked until restart.",
                partitionId);
        }
        finally
        {
            stopwatch.Stop();
            metrics.RecordDuration(
                partitionId,
                stopwatch.Elapsed.TotalMilliseconds);
        }
    }

    private Task ProcessErrorAsync(ProcessErrorEventArgs args)
    {
        logger.LogError(
            args.Exception,
            "Event Hubs processor error. Operation={Operation}, Partition={PartitionId}",
            args.Operation,
            args.PartitionId);

        return Task.CompletedTask;
    }
}
