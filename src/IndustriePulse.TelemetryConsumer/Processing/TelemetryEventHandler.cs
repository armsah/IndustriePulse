using System.Text.Json;

namespace IndustriePulse.TelemetryConsumer.Processing;

public sealed class TelemetryEventHandler
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

        _ = eventId;
        _ = siteId;
        _ = machineId;

        // P3 processing boundary:
        // future state/rule handling will happen before this checkpoint.
        await checkpointAsync(cancellationToken);
    }

    private static string RequireString(JsonElement root, string propertyName)
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
}
