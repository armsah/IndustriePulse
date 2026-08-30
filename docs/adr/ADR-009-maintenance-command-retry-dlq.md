# ADR-009: Maintenance command retry and DLQ re-drive policy

- Status: Accepted
- Phase: P6

## Context

Maintenance commands use Azure Service Bus because they require queue semantics, retries, duplicate detection, and dead-letter handling.

P6 requires explicit operational tooling for poison-message inspection and recovery.

## Decision

Use the native Azure Service Bus dead-letter subqueue for unrecoverable maintenance-command deliveries.

Keep the queue maximum delivery count at 10.

Allow controlled validation failures to be explicitly dead-lettered with a diagnostic reason and description.

Inspect DLQ messages non-destructively before recovery.

Re-drive only after an operator understands or accepts the underlying failure.

Preserve the original message body and business identity during re-drive.

Use a new deterministic broker MessageId:

`<originalMessageId>:redrive:<deadLetterSequenceNumber>`

This avoids the intentional re-drive being suppressed by the queue duplicate-detection window when the original broker MessageId is still present in duplicate history.

Add re-drive metadata including:

- `redrive`
- `originalMessageId`
- `deadLetterSequenceNumber`
- original dead-letter reason when available

The re-drive operation sends the replacement message first and completes the original DLQ message only after the send succeeds.

P6 operations tooling receives a dedicated Service Bus authorization rule with Send and Listen rights and no Manage right.

## Consequences

A failed replacement send leaves the original DLQ message recoverable.

A process failure after send but before DLQ completion can cause another re-drive attempt.

The deterministic replacement MessageId allows Service Bus duplicate detection to suppress a repeated send only within the configured duplicate-detection history window.

The workflow is not an atomic distributed transaction and does not provide exactly-once delivery.

The CLI is intended for targeted operator remediation, not high-volume bulk recovery.

The current CLI scans a limited number of DLQ messages and abandons non-target messages while searching.

Production hardening should use managed identity/RBAC, operational auditing, DLQ monitoring, and bulk recovery controls.
