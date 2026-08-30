using Azure.Messaging.ServiceBus;
using IndustriePulse.Maintenance.Cli.Commands;

const string ConnectionStringVariable =
    "INDUSTRIEPULSE_SERVICEBUS_OPERATIONS_CONNECTION_STRING";

const string QueueVariable =
    "INDUSTRIEPULSE_SERVICEBUS_QUEUE_NAME";

if (args.Length < 2 ||
    !string.Equals(args[0], "dlq", StringComparison.OrdinalIgnoreCase))
{
    PrintUsage();
    return 2;
}

string connectionString =
    Environment.GetEnvironmentVariable(ConnectionStringVariable)
    ?? throw new InvalidOperationException(
        $"{ConnectionStringVariable} is required.");

string queueName =
    Environment.GetEnvironmentVariable(QueueVariable)
    ?? "maintenance-commands";

await using var client =
    new ServiceBusClient(connectionString);

using var cts = new CancellationTokenSource();

Console.CancelKeyPress += (_, eventArgs) =>
{
    eventArgs.Cancel = true;
    cts.Cancel();
};

string command = args[1].ToLowerInvariant();

return command switch
{
    "inspect" =>
        await DlqInspectCommand.RunAsync(
            client,
            queueName,
            ParseIntOption(args, "--max", 10),
            cts.Token),

    "seed-poison" =>
        await SeedPoisonCommand.RunAsync(
            client,
            queueName,
            ParseStringOption(
                args,
                "--message-id",
                $"p6-poison-{Guid.NewGuid():N}"),
            cts.Token),

    "redrive" =>
        await DlqRedriveCommand.RunAsync(
            client,
            queueName,
            RequireStringOption(args, "--message-id"),
            cts.Token),

    _ => UnknownCommand(command)
};

static int ParseIntOption(
    string[] arguments,
    string option,
    int defaultValue)
{
    string? value = FindOption(arguments, option);

    return value is null
        ? defaultValue
        : int.Parse(value);
}

static string ParseStringOption(
    string[] arguments,
    string option,
    string defaultValue) =>
    FindOption(arguments, option) ?? defaultValue;

static string RequireStringOption(
    string[] arguments,
    string option) =>
    FindOption(arguments, option)
    ?? throw new ArgumentException(
        $"Required option missing: {option}");

static string? FindOption(
    string[] arguments,
    string option)
{
    for (int index = 0; index < arguments.Length - 1; index++)
    {
        if (string.Equals(
                arguments[index],
                option,
                StringComparison.OrdinalIgnoreCase))
        {
            return arguments[index + 1];
        }
    }

    return null;
}

static int UnknownCommand(string command)
{
    Console.Error.WriteLine($"Unknown DLQ command: {command}");
    PrintUsage();

    return 2;
}

static void PrintUsage()
{
    Console.WriteLine(
        """
        IndustriePulse Maintenance Operations CLI

        Required environment variables:
          INDUSTRIEPULSE_SERVICEBUS_OPERATIONS_CONNECTION_STRING
          INDUSTRIEPULSE_SERVICEBUS_QUEUE_NAME (optional; default maintenance-commands)

        Commands:
          dlq inspect [--max 10]
          dlq seed-poison [--message-id <id>]
          dlq redrive --message-id <id>
        """);
}
