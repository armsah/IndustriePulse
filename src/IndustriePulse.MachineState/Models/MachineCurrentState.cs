using Newtonsoft.Json;

namespace IndustriePulse.MachineState.Models;

public sealed class MachineCurrentState
{
    [JsonProperty(PropertyName = "id")]
    public required string Id { get; init; }

    [JsonProperty(PropertyName = "machineId")]
    public required string MachineId { get; init; }

    [JsonProperty(PropertyName = "siteId")]
    public required string SiteId { get; init; }

    [JsonProperty(PropertyName = "machineType")]
    public required string MachineType { get; init; }

    [JsonProperty(PropertyName = "timestampUtc")]
    public required DateTimeOffset TimestampUtc { get; init; }

    [JsonProperty(PropertyName = "temperatureC")]
    public double TemperatureC { get; init; }

    [JsonProperty(PropertyName = "vibrationMmS")]
    public double VibrationMmS { get; init; }

    [JsonProperty(PropertyName = "pressureBar")]
    public double PressureBar { get; init; }

    [JsonProperty(PropertyName = "rpm")]
    public int Rpm { get; init; }

    [JsonProperty(PropertyName = "sequence")]
    public long Sequence { get; init; }

    [JsonProperty(PropertyName = "firmwareVersion")]
    public required string FirmwareVersion { get; init; }

    [JsonProperty(PropertyName = "_etag")]
    public string? ETag { get; init; }
}
