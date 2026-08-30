namespace IndustriePulse.Maintenance.Rules;

public sealed record MaintenanceRuleInput(
    string EventId,
    string SiteId,
    string MachineId,
    string MachineType,
    DateTimeOffset TimestampUtc,
    double TemperatureC,
    double VibrationMmS,
    long Sequence);
