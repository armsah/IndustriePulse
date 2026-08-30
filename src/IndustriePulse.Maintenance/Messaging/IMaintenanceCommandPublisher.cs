using IndustriePulse.Maintenance.Contracts;

namespace IndustriePulse.Maintenance.Messaging;

public interface IMaintenanceCommandPublisher
{
    Task PublishAsync(
        MaintenanceCommand command,
        CancellationToken cancellationToken = default);
}
