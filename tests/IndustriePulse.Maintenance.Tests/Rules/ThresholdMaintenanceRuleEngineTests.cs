using IndustriePulse.Maintenance.Contracts;
using IndustriePulse.Maintenance.Rules;

namespace IndustriePulse.Maintenance.Tests.Rules;

public sealed class ThresholdMaintenanceRuleEngineTests
{
    private readonly ThresholdMaintenanceRuleEngine _engine = new();

    [Fact]
    public void NormalTelemetry_ProducesNoCommand()
    {
        var commands = _engine.Evaluate(CreateInput(70, 2));

        Assert.Empty(commands);
    }

    [Fact]
    public void Overheat_ProducesCriticalCoolingCommand()
    {
        var command = Assert.Single(_engine.Evaluate(CreateInput(90, 2)));

        Assert.Equal("OVERHEAT", command.RuleId);
        Assert.Equal(MaintenanceSeverity.Critical, command.Severity);
        Assert.Equal(MaintenanceAction.InspectCoolingSystem, command.Action);
    }

    [Fact]
    public void HighVibration_ProducesWarningInspectionCommand()
    {
        var command = Assert.Single(_engine.Evaluate(CreateInput(70, 8)));

        Assert.Equal("HIGH_VIBRATION", command.RuleId);
        Assert.Equal(MaintenanceSeverity.Warning, command.Severity);
        Assert.Equal(MaintenanceAction.InspectMachine, command.Action);
    }

    [Fact]
    public void BothThresholds_ProduceTwoCommands()
    {
        var commands = _engine.Evaluate(CreateInput(90, 8));

        Assert.Equal(2, commands.Count);
    }

    [Fact]
    public void SameEventAndRule_ProducesSameCommandId()
    {
        var input = CreateInput(90, 2);

        var first = Assert.Single(_engine.Evaluate(input));
        var second = Assert.Single(_engine.Evaluate(input));

        Assert.Equal(first.CommandId, second.CommandId);
    }

    private static MaintenanceRuleInput CreateInput(
        double temperatureC,
        double vibrationMmS)
        => new(
            "event-001",
            "DE-MUC-01",
            "CNC-00001",
            "CNC",
            DateTimeOffset.Parse("2026-01-01T00:00:05Z"),
            temperatureC,
            vibrationMmS,
            2);
}
