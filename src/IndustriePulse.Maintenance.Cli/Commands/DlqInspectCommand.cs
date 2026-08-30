using System.Text.Json;
using Azure.Messaging.ServiceBus;

namespace IndustriePulse.Maintenance.Cli.Commands;

public static class DlqInspectCommand
{
    public static async Task<int> RunAsync(
        ServiceBusClient client,
        string queueName,
        int maxMessages,
        CancellationToken cancellationToken)
    {
        await using ServiceBusReceiver receiver =
            client.CreateReceiver(
                queueName,
                new ServiceBusReceiverOptions
                {
                    SubQueue = SubQueue.DeadLetter,
                    ReceiveMode = ServiceBusReceiveMode.PeekLock
                });

        IReadOnlyList<ServiceBusReceivedMessage> messages =
            await receiver.PeekMessagesAsync(
                maxMessages,
                cancellationToken: cancellationToken);

        if (messages.Count == 0)
        {
            Console.WriteLine("DLQ is empty.");
            return 0;
        }

        foreach (ServiceBusReceivedMessage message in messages)
        {
            var output = new
            {
                message.MessageId,
                message.SequenceNumber,
                message.EnqueuedSequenceNumber,
                message.DeliveryCount,
                message.DeadLetterReason,
                message.DeadLetterErrorDescription,
                Body = message.Body.ToString()
            };

            Console.WriteLine(
                JsonSerializer.Serialize(
                    output,
                    new JsonSerializerOptions
                    {
                        WriteIndented = true
                    }));
        }

        return 0;
    }
}
