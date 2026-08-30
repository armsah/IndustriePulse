using Azure.Messaging.ServiceBus;
using IndustriePulse.Maintenance.Cli.Messaging;

namespace IndustriePulse.Maintenance.Cli.Tests.Messaging;

public sealed class RedriveMessageFactoryTests
{
    [Fact]
    public void Create_PreservesPayloadAndCreatesDeterministicRedriveIdentity()
    {
        ServiceBusReceivedMessage deadLetterMessage =
            ServiceBusModelFactory.ServiceBusReceivedMessage(
                body: BinaryData.FromString(
                    """{"commandId":"command-001"}"""),
                messageId: "command-001",
                sequenceNumber: 42);

        ServiceBusMessage result =
            RedriveMessageFactory.Create(deadLetterMessage);

        Assert.Equal(
            "command-001:redrive:42",
            result.MessageId);

        Assert.Equal(
            """{"commandId":"command-001"}""",
            result.Body.ToString());

        Assert.True(
            Assert.IsType<bool>(
                result.ApplicationProperties["redrive"]));

        Assert.Equal(
            "command-001",
            result.ApplicationProperties["originalMessageId"]);

        Assert.Equal(
            42L,
            result.ApplicationProperties["deadLetterSequenceNumber"]);

        Assert.False(
            result.ApplicationProperties.ContainsKey(
                "originalDeadLetterReason"));
    }
}
