using Azure.Messaging.ServiceBus;

namespace IndustriePulse.Maintenance.Cli.Commands;

public static class SeedPoisonCommand
{
    public static async Task<int> RunAsync(
        ServiceBusClient client,
        string queueName,
        string messageId,
        CancellationToken cancellationToken)
    {
        await using ServiceBusSender sender =
            client.CreateSender(queueName);

        var poison = new ServiceBusMessage(
            """{"schemaVersion":"1.0","machineId":42,"invalid":true}""")
        {
            MessageId = messageId,
            ContentType = "application/json",
            Subject = "maintenance-command.v1"
        };

        poison.ApplicationProperties["p6PoisonTest"] = true;

        await sender.SendMessageAsync(poison, cancellationToken);

        await using ServiceBusReceiver receiver =
            client.CreateReceiver(
                queueName,
                new ServiceBusReceiverOptions
                {
                    ReceiveMode = ServiceBusReceiveMode.PeekLock
                });

        ServiceBusReceivedMessage? received =
            await receiver.ReceiveMessageAsync(
                TimeSpan.FromSeconds(15),
                cancellationToken);

        if (received is null)
        {
            Console.Error.WriteLine(
                "No message was received from the maintenance queue.");

            return 1;
        }

        if (!string.Equals(
                received.MessageId,
                messageId,
                StringComparison.Ordinal))
        {
            await receiver.AbandonMessageAsync(
                received,
                cancellationToken: cancellationToken);

            Console.Error.WriteLine(
                $"Received unexpected message '{received.MessageId}'.");

            return 1;
        }

        await receiver.DeadLetterMessageAsync(
            received,
            "InvalidMaintenanceCommand",
            "P6 controlled poison message failed maintenance-command validation.",
            cancellationToken);

        Console.WriteLine($"Dead-lettered poison message: {messageId}");

        return 0;
    }
}
