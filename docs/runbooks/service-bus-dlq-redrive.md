# Service Bus DLQ and Re-drive Runbook

## Purpose

This runbook covers inspection and recovery of maintenance-command messages that have entered the Azure Service Bus dead-letter queue.

P6 adds operational tooling around the existing `maintenance-commands` queue.

## Queue

- Namespace SKU: Standard
- Queue: `maintenance-commands`
- Dead-letter subqueue: Service Bus-managed DLQ
- Maximum delivery count: 10
- Duplicate detection: enabled
- Duplicate detection window: 10 minutes

## Operational credential

The maintenance runtime keeps its existing least-privilege credentials:

- producer: Send only
- receiver: Listen only

P6 adds:

- `maintenance-operations`
- Send: true
- Listen: true
- Manage: false

Required environment variables:

- `INDUSTRIEPULSE_SERVICEBUS_OPERATIONS_CONNECTION_STRING`
- `INDUSTRIEPULSE_SERVICEBUS_QUEUE_NAME`

Do not print or commit connection strings.

## Inspect the DLQ

Run `dlq inspect --max 10` using `IndustriePulse.Maintenance.Cli`.

The command peeks DLQ messages without settling them.

Review MessageId, SequenceNumber, DeliveryCount, DeadLetterReason, DeadLetterErrorDescription, and the message body.

Do not re-drive a message until the underlying cause is understood or intentionally accepted.

## Controlled poison-message test

For development evidence, `dlq seed-poison --message-id p6-poison-001` sends a deliberately invalid maintenance command and dead-letters it with `InvalidMaintenanceCommand`.

This is a P6 test fixture, not normal production processing.

## Re-drive

Run `dlq redrive --message-id <id>` to recover a selected message.

The operation receives the DLQ message under PeekLock, constructs a replacement, sends it to the main queue, and only then completes the DLQ message.

The replacement broker MessageId follows `<originalMessageId>:redrive:<deadLetterSequenceNumber>`.

The replacement preserves the body and records `redrive`, `originalMessageId`, `deadLetterSequenceNumber`, and the original dead-letter reason when available.

Changing the broker MessageId prevents the intentional re-drive from being suppressed by the queue duplicate-detection window.

## Failure semantics

If the replacement send fails, the original DLQ message remains recoverable.

If execution stops after send but before DLQ completion, another attempt can occur. The deterministic replacement MessageId allows Service Bus duplicate detection to suppress a repeated send during its configured history window.

This is not an atomic distributed transaction and does not provide exactly-once delivery.

## Verification

The successful P6 recovery ends with zero active messages and zero dead-letter messages after the recovered message is consumed.

## Production considerations

- use managed identity/RBAC instead of long-lived shared-access keys
- audit DLQ inspection and re-drive operations
- alert on DLQ depth and message age
- validate schema before resubmission
- add bulk recovery controls and rate limits for production-scale operations

