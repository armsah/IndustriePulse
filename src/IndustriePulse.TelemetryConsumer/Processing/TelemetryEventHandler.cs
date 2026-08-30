using System.Globalization;
using System.Text.Json;
using IndustriePulse.MachineState.Models;
using IndustriePulse.MachineState.Repositories;
using IndustriePulse.Maintenance.Messaging;
using IndustriePulse.Maintenance.Rules;

namespace IndustriePulse.TelemetryConsumer.Processing;

public sealed class TelemetryEventHandler(
    IMachineStateRepository machineStateRepository,
    IMaintenanceRuleEngine maintenanceRuleEngine,
    IMaintenanceCommandPublisher maintenanceCommandPublisher)
{
    public async Task ProcessAsync(
        ReadOnlyMemory<byte> body,
        Func<CancellationToken, Task> checkpointAsync,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(checkpointAsync);

        using JsonDocument document = JsonDocument.Parse(body);
        JsonElement root = document.RootElement;

        string eventId = RequireString(root, "eventId");
        string siteId = RequireString(root, "siteId");
        string machineId = RequireString(root, "machineId");
        string machineType = RequireString(root, "machineType");
        DateTimeOffset timestampUtc = RequireTimestamp(root, "timestampUtc");
        double temperatureC = RequireDouble(root, "temperatureC");
        double vibrationMmS = RequireDouble(root, "vibrationMmS");
        double pressureBar = RequireDouble(root, "pressureBar");
        int rpm = RequireInt32(root, "rpm");
        long sequence = RequireInt64(root, "sequence");
        string firmwareVersion = RequireString(root, "firmwareVersion");

        var state = new MachineCurrentState
        {
            Id = machineId,
            MachineId = machineId,
            SiteId = siteId,
            MachineType = machineType,
            TimestampUtc = timestampUtc,
            TemperatureC = temperatureC,
            VibrationMmS = vibrationMmS,
            PressureBar = pressureBar,
            Rpm = rpm,
            Sequence = sequence,
            FirmwareVersion = firmwareVersion
        };

        // P4/P5 processing boundary:
        // durable current state and any resulting maintenance commands
        // must succeed before the Event Hubs checkpoint can advance.
        bool stateAdvanced = await machineStateRepository.TryAdvanceAsync(
            state,
            cancellationToken);

        // Stale or duplicate telemetry is considered successfully processed,
        // but must not produce duplicate maintenance commands.
        if (stateAdvanced)
        {
            var ruleInput = new MaintenanceRuleInput(
                eventId,
                siteId,
                machineId,
                machineType,
                timestampUtc,
                temperatureC,
                vibrationMmS,
                sequence);

            var commands = maintenanceRuleEngine.Evaluate(ruleInput);

            foreach (var command in commands)
            {
                await maintenanceCommandPublisher.PublishAsync(
                    command,
                    cancellationToken);
            }
        }

        await checkpointAsync(cancellationToken);
    }

    private static string RequireString(
        JsonElement root,
        string propertyName)
    {
        if (!root.TryGetProperty(propertyName, out JsonElement property) ||
            property.ValueKind != JsonValueKind.String ||
            string.IsNullOrWhiteSpace(property.GetString()))
        {
            throw new InvalidDataException(
                $"Telemetry event requires non-empty '{propertyName}'.");
        }

        return property.GetString()!;
    }

    private static double RequireDouble(
        JsonElement root,
        string propertyName)
    {
        if (!root.TryGetProperty(propertyName, out JsonElement property) ||
            property.ValueKind != JsonValueKind.Number ||
            !property.TryGetDouble(out double value))
        {
            throw new InvalidDataException(
                $"Telemetry event requires numeric '{propertyName}'.");
        }

        return value;
    }

    private static int RequireInt32(
        JsonElement root,
        string propertyName)
    {
        if (!root.TryGetProperty(propertyName, out JsonElement property) ||
            property.ValueKind != JsonValueKind.Number ||
            !property.TryGetInt32(out int value))
        {
            throw new InvalidDataException(
                $"Telemetry event requires integer '{propertyName}'.");
        }

        return value;
    }

    private static long RequireInt64(
        JsonElement root,
        string propertyName)
    {
        if (!root.TryGetProperty(propertyName, out JsonElement property) ||
            property.ValueKind != JsonValueKind.Number ||
            !property.TryGetInt64(out long value))
        {
            throw new InvalidDataException(
                $"Telemetry event requires integer '{propertyName}'.");
        }

        return value;
    }

    private static DateTimeOffset RequireTimestamp(
        JsonElement root,
        string propertyName)
    {
        string raw = RequireString(root, propertyName);

        if (!DateTimeOffset.TryParse(
                raw,
                CultureInfo.InvariantCulture,
                DateTimeStyles.AssumeUniversal |
                DateTimeStyles.AdjustToUniversal,
                out DateTimeOffset value))
        {
            throw new InvalidDataException(
                $"Telemetry event requires valid UTC timestamp '{propertyName}'.");
        }

        return value;
    }
}
