# P6 Evidence - Service Bus DLQ and Re-drive

## Exit criterion

P6 exit criterion: **Poison message recovered.**

Status: **Satisfied**

## Implementation

P6 adds:

- `IndustriePulse.Maintenance.Cli`
- DLQ inspection
- controlled poison-message injection
- targeted DLQ re-drive
- deterministic re-drive broker identity
- Service Bus operations authorization rule
- automated re-drive factory test
- operational runbook

## CLI commands

- `dlq inspect [--max 10]`
- `dlq seed-poison [--message-id <id>]`
- `dlq redrive --message-id <id>`

## Authorization

A dedicated queue authorization rule was deployed:

- Send: true
- Listen: true
- Manage: false

Existing producer and receiver permissions remain unchanged.

## Automated validation

.NET validation:

- 25 tests
- 25 succeeded
- 0 failed
- 0 skipped

Terraform validation:

- 3 passed
- 0 failed

Terraform format and configuration validation also passed.

## Live Azure proof

The short-lived P6 environment started with:

- active messages: 0
- dead-letter messages: 0

A controlled poison message with broker MessageId `p6-poison-001` was injected and explicitly dead-lettered.

DLQ inspection confirmed:

- MessageId: `p6-poison-001`
- SequenceNumber: `1`
- DeadLetterReason: `InvalidMaintenanceCommand`
- DeadLetterErrorDescription: `P6 controlled poison message failed maintenance-command validation.`

The message was re-driven using deterministic broker identity:

`p6-poison-001:redrive:1`

A receiver then validated the recovered message:

- OriginalMessageId: `p6-poison-001`
- RedriveMessageId: `p6-poison-001:redrive:1`
- Redrive: `True`

The recovered message was completed successfully.

Final broker state:

- active messages: 0
- dead-letter messages: 0

A subsequent re-drive attempt correctly reported that the original message no longer existed in the DLQ.

## Recovery semantics

The re-drive operation sends the replacement message before completing the DLQ message.

If the send fails, the original DLQ message remains recoverable.

If execution stops after send but before DLQ completion, another attempt may occur. The deterministic replacement MessageId works with the Service Bus duplicate-detection window to suppress repeated sends during that window.

This is not an atomic distributed transaction and no exactly-once guarantee is claimed.

## Cost control

The Azure environment used for P6 live validation was destroyed after evidence collection.

Runtime Service Bus credentials were cleared from the local environment.
