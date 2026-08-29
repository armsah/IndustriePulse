using IndustriePulse.TelemetryConsumer.Processing;

namespace IndustriePulse.TelemetryConsumer.Tests.Processing;

public sealed class PartitionCheckpointGateTests
{
    [Fact]
    public void NewPartition_CanCheckpoint()
    {
        var gate = new PartitionCheckpointGate();

        Assert.True(gate.CanCheckpoint("0"));
    }

    [Fact]
    public void BlockedPartition_CannotCheckpoint()
    {
        var gate = new PartitionCheckpointGate();

        gate.Block("0");

        Assert.False(gate.CanCheckpoint("0"));
    }

    [Fact]
    public void BlockingOnePartition_DoesNotBlockAnother()
    {
        var gate = new PartitionCheckpointGate();

        gate.Block("0");

        Assert.False(gate.CanCheckpoint("0"));
        Assert.True(gate.CanCheckpoint("1"));
    }
}
