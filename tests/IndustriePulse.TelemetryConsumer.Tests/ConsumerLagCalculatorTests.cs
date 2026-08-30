using IndustriePulse.TelemetryConsumer.Metrics;

namespace IndustriePulse.TelemetryConsumer.Tests;

public sealed class ConsumerLagCalculatorTests
{
    [Fact]
    public void CalculateEventLag_WhenBehind_ReturnsDifference()
    {
        long result =
            ConsumerLagCalculator.CalculateEventLag(
                currentSequenceNumber: 100,
                lastEnqueuedSequenceNumber: 150);

        Assert.Equal(50, result);
    }

    [Fact]
    public void CalculateEventLag_WhenCaughtUp_ReturnsZero()
    {
        long result =
            ConsumerLagCalculator.CalculateEventLag(
                currentSequenceNumber: 150,
                lastEnqueuedSequenceNumber: 150);

        Assert.Equal(0, result);
    }

    [Fact]
    public void CalculateEventLag_WhenCurrentIsAhead_ClampsToZero()
    {
        long result =
            ConsumerLagCalculator.CalculateEventLag(
                currentSequenceNumber: 151,
                lastEnqueuedSequenceNumber: 150);

        Assert.Equal(0, result);
    }

    [Fact]
    public void CalculateEventAgeMs_ReturnsElapsedMilliseconds()
    {
        var enqueuedTime =
            new DateTimeOffset(
                2026, 8, 30,
                12, 0, 0,
                TimeSpan.Zero);

        DateTimeOffset observedAt =
            enqueuedTime.AddSeconds(5);

        double result =
            ConsumerLagCalculator.CalculateEventAgeMs(
                enqueuedTime,
                observedAt);

        Assert.Equal(5000, result);
    }

    [Fact]
    public void CalculateEventAgeMs_WhenClockIsEarlier_ClampsToZero()
    {
        var enqueuedTime =
            new DateTimeOffset(
                2026, 8, 30,
                12, 0, 5,
                TimeSpan.Zero);

        DateTimeOffset observedAt =
            enqueuedTime.AddSeconds(-5);

        double result =
            ConsumerLagCalculator.CalculateEventAgeMs(
                enqueuedTime,
                observedAt);

        Assert.Equal(0, result);
    }
}