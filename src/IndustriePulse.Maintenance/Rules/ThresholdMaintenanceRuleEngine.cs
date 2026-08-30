using System.Security.Cryptography;
using System.Text;
using IndustriePulse.Maintenance.Contracts;

namespace IndustriePulse.Maintenance.Rules;

public sealed class ThresholdMaintenanceRuleEngine : IMaintenanceRuleEngine
{
    public const double OverheatThresholdC = 85.0;
    public const double HighVibrationThresholdMmS = 7.0;

    public IReadOnlyList<MaintenanceCommand> Evaluate(MaintenanceRuleInput input)
    {
        var commands = new List<MaintenanceCommand>();

        if (input.TemperatureC >= OverheatThresholdC)
        {
            commands.Add(CreateCommand(
                input,
                "OVERHEAT",
                MaintenanceSeverity.Critical,
                MaintenanceAction.InspectCoolingSystem,
                $"Temperature {input.TemperatureC:F2} C exceeded threshold {OverheatThresholdC:F2} C."));
        }

        if (input.VibrationMmS >= HighVibrationThresholdMmS)
        {
            commands.Add(CreateCommand(
                input,
                "HIGH_VIBRATION",
                MaintenanceSeverity.Warning,
                MaintenanceAction.InspectMachine,
                $"Vibration {input.VibrationMmS:F2} mm/s exceeded threshold {HighVibrationThresholdMmS:F2} mm/s."));
        }

        return commands;
    }

    private static MaintenanceCommand CreateCommand(
        MaintenanceRuleInput input,
        string ruleId,
        MaintenanceSeverity severity,
        MaintenanceAction action,
        string reason)
    {
        var commandId = Convert.ToHexString(
            SHA256.HashData(
                Encoding.UTF8.GetBytes($"{input.EventId}:{ruleId}")))
            .ToLowerInvariant();

        return new MaintenanceCommand(
            commandId,
            "1.0",
            ruleId,
            input.EventId,
            input.SiteId,
            input.MachineId,
            input.MachineType,
            input.TimestampUtc,
            input.Sequence,
            severity,
            action,
            reason);
    }
}
