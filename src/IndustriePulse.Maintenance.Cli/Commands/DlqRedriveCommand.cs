using Azure.Messaging.ServiceBus;
using IndustriePulse.Maintenance.Cli.Messaging;

namespace IndustriePulse.Maintenance.Cli.Commands;

public static class DlqRedriveCommand
{
    public static async Task<int> RunAsync(
        ServiceBusClient client,
        string queueName,
        string originalMessageId,
        CancellationToken cancellationToken)
    {
        await using ServiceBusReceiver dlqReceiver =
            client.CreateReceiver(
                queueName,
                new ServiceBusReceiverOptions
                {
                    SubQueue = SubQueue.DeadLetter,
                    ReceiveMode = ServiceBusReceiveMode.PeekLock
                });

        await using ServiceBusSender sender =
            client.CreateSender(queueName);

        for (int attempt = 0; attempt < 20; attempt++)
        {
            ServiceBusReceivedMessage? message =
                await dlqReceiver.ReceiveMessageAsync(
                    TimeSpan.FromSeconds(2),
                    cancellationToken);

            if (message is null)
            {
                break;
            }

            if (!string.Equals(
                    message.MessageId,
                    originalMessageId,
                    StringComparison.Ordinal))
            {
                await dlqReceiver.AbandonMessageAsync(
                    message,
                    cancellationToken: cancellationToken);

                continue;
            }

            ServiceBusMessage redrive =
                RedriveMessageFactory.Create(message);

            await sender.SendMessageAsync(
                redrive,
                cancellationToken);

            await dlqReceiver.CompleteMessageAsync(
                message,
                cancellationToken);

            Console.WriteLine(
                $"Re-drove '{originalMessageId}' as '{redrive.MessageId}'.");

            return 0;
        }

        Console.Error.WriteLine(
            $"DLQ message '{originalMessageId}' was not found.");

        return 1;
    }
}
