using System.Text.Json;
using System.Text.Json.Serialization;
using IndustriePulse.Maintenance.Contracts;

namespace IndustriePulse.Maintenance.Messaging;

public static class MaintenanceCommandJson
{
    private static readonly JsonSerializerOptions SerializerOptions =
        new(JsonSerializerDefaults.Web)
        {
            Converters =
            {
                new JsonStringEnumConverter()
            }
        };

    public static string Serialize(
        MaintenanceCommand command) =>
        JsonSerializer.Serialize(
            command,
            SerializerOptions);
}
