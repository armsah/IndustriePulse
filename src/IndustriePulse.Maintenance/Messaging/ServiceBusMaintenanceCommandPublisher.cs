using Azure.Messaging.ServiceBus;
using IndustriePulse.Maintenance.Contracts;

namespace IndustriePulse.Maintenance.Messaging;

public sealed class ServiceBusMaintenanceCommandPublisher
    : IMaintenanceCommandPublisher
{
    private readonly ServiceBusSender _sender;

    public ServiceBusMaintenanceCommandPublisher(ServiceBusSender sender)
    {
        _sender = sender;
    }

    public async Task PublishAsync(
        MaintenanceCommand command,
        CancellationToken cancellationToken = default)
    {
        string body =
            MaintenanceCommandJson.Serialize(command);

        var message = new ServiceBusMessage(body)
        {
            MessageId = command.CommandId,
            ContentType = "application/json",
            Subject = "maintenance-command.v1",
            CorrelationId = command.EventId
        };

        message.ApplicationProperties["schemaVersion"] =
            command.SchemaVersion;

        message.ApplicationProperties["ruleId"] =
            command.RuleId;

        message.ApplicationProperties["machineId"] =
            command.MachineId;

        await _sender.SendMessageAsync(
            message,
            cancellationToken);
    }
}
