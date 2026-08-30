using Azure.Messaging.ServiceBus;

namespace IndustriePulse.Maintenance.Cli.Messaging;

public static class RedriveMessageFactory
{
    public static ServiceBusMessage Create(ServiceBusReceivedMessage deadLetterMessage)
    {
        ArgumentNullException.ThrowIfNull(deadLetterMessage);

        var redriveMessage = new ServiceBusMessage(deadLetterMessage)
        {
            MessageId =
                $"{deadLetterMessage.MessageId}:redrive:{deadLetterMessage.SequenceNumber}"
        };

        redriveMessage.ApplicationProperties["redrive"] = true;
        redriveMessage.ApplicationProperties["originalMessageId"] =
            deadLetterMessage.MessageId;
        redriveMessage.ApplicationProperties["deadLetterSequenceNumber"] =
            deadLetterMessage.SequenceNumber;

        if (!string.IsNullOrWhiteSpace(deadLetterMessage.DeadLetterReason))
        {
            redriveMessage.ApplicationProperties["originalDeadLetterReason"] =
                deadLetterMessage.DeadLetterReason;
        }

        return redriveMessage;
    }
}
