using System.Text.Json;
using IndustriePulse.Maintenance.Contracts;
using IndustriePulse.Maintenance.Messaging;

namespace IndustriePulse.Maintenance.Tests.Messaging;

public sealed class MaintenanceCommandJsonTests
{
    [Fact]
    public void Serialize_UsesVersionedCamelCaseContract()
    {
        var command = new MaintenanceCommand(
            CommandId: "cmd-001",
            SchemaVersion: "1.0",
            RuleId: "OVERHEAT",
            EventId: "evt-001",
            SiteId: "DE-BY-01",
            MachineId: "machine-0001",
            MachineType: "cnc",
            TriggeredAtUtc:
                DateTimeOffset.Parse("2026-08-29T12:00:00Z"),
            Sequence: 42,
            Severity: MaintenanceSeverity.Critical,
            Action: MaintenanceAction.InspectCoolingSystem,
            Reason: "Temperature exceeded threshold.");

        string json =
            MaintenanceCommandJson.Serialize(command);

        using JsonDocument document =
            JsonDocument.Parse(json);

        JsonElement root = document.RootElement;

        Assert.Equal(
            "cmd-001",
            root.GetProperty("commandId").GetString());

        Assert.Equal(
            "1.0",
            root.GetProperty("schemaVersion").GetString());

        Assert.Equal(
            "OVERHEAT",
            root.GetProperty("ruleId").GetString());

        Assert.Equal(
            "Critical",
            root.GetProperty("severity").GetString());

        Assert.Equal(
            "InspectCoolingSystem",
            root.GetProperty("action").GetString());

        Assert.False(
            root.TryGetProperty(
                "CommandId",
                out _));
    }
}
