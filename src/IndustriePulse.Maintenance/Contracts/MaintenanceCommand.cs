namespace IndustriePulse.Maintenance.Contracts;

public sealed record MaintenanceCommand(
    string CommandId,
    string SchemaVersion,
    string RuleId,
    string EventId,
    string SiteId,
    string MachineId,
    string MachineType,
    DateTimeOffset TriggeredAtUtc,
    long Sequence,
    MaintenanceSeverity Severity,
    MaintenanceAction Action,
    string Reason);
