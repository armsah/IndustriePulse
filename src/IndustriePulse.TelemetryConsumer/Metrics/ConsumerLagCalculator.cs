namespace IndustriePulse.TelemetryConsumer.Metrics;

public static class ConsumerLagCalculator
{
    public static long CalculateEventLag(
        long currentSequenceNumber,
        long lastEnqueuedSequenceNumber)
    {
        return Math.Max(
            0,
            lastEnqueuedSequenceNumber - currentSequenceNumber);
    }

    public static double CalculateEventAgeMs(
        DateTimeOffset enqueuedTime,
        DateTimeOffset observedAt)
    {
        return Math.Max(
            0,
            (observedAt - enqueuedTime).TotalMilliseconds);
    }
}