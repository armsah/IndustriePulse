using System.Collections.Concurrent;

namespace IndustriePulse.TelemetryConsumer.Processing;

public sealed class PartitionCheckpointGate
{
    private readonly ConcurrentDictionary<string, byte> _blockedPartitions = new();

    public bool CanCheckpoint(string partitionId) =>
        !_blockedPartitions.ContainsKey(partitionId);

    public void Block(string partitionId) =>
        _blockedPartitions.TryAdd(partitionId, 0);
}
