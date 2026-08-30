# P5 Evidence: Rule Engine to Maintenance Command Flow

## Exit criterion

**P5 exit criterion:** Rule -> command flow works.

Status: **Satisfied**

A live Azure test successfully exercised:

`Event Hubs -> telemetry consumer -> Cosmos DB state advance -> threshold rule engine -> Azure Service Bus maintenance command`

## Rule engine

P5 implements deterministic threshold rules:

| Rule | Condition | Severity | Action |
| --- | --- | --- | --- |
| `OVERHEAT` | `temperatureC >= 85.0` | `Critical` | `InspectCoolingSystem` |
| `HIGH_VIBRATION` | `vibrationMmS >= 7.0` | `Warning` | `InspectMachine` |

Commands use schema version `1.0`.

The command contract is stored in:

`contracts/maintenance-command.v1.json`

Command identity is deterministic:

`commandId = SHA256(eventId + ":" + ruleId)`

The same value is used as the Azure Service Bus `MessageId`.

## Consumer behavior

The telemetry consumer:

1. validates the telemetry event;
2. attempts to advance the current machine-state projection;
3. evaluates maintenance rules only when state advances;
4. publishes resulting Service Bus commands;
5. checkpoints Event Hubs only after successful publication.

Stale or duplicate telemetry does not regenerate maintenance commands.

A Service Bus publication failure prevents Event Hubs checkpoint advancement.

## Automated validation

Final .NET validation:

- 24 tests executed
- 24 succeeded
- 0 failed
- 0 skipped

The tests cover:

- no command for normal telemetry;
- overheat command generation;
- high-vibration command generation;
- simultaneous rule matches;
- deterministic command identity;
- maintenance-command JSON contract serialization;
- command publication from the telemetry consumer;
- publication failure preventing checkpoint advancement;
- stale telemetry suppressing command publication.

Final Terraform validation:

- `terraform fmt -check -recursive`: passed
- `terraform validate`: passed
- `terraform test`: 3 passed, 0 failed

The Service Bus Terraform test verifies queue configuration and least-privilege authorization rules.

## Live Azure proof

A short-lived Azure deployment was used for P5 validation.

The Service Bus queue was configured with:

- Standard Service Bus namespace;
- queue `maintenance-commands`;
- duplicate detection enabled;
- 10-minute duplicate-detection history;
- maximum delivery count 10;
- dead-lettering on message expiration enabled;
- send-only producer authorization;
- listen-only validation receiver authorization.

A deterministic live telemetry probe published:

- event: `p5-live-overheat-001`
- machine: `P5-LIVE-CNC-0001`
- sequence: `1`
- temperature: `96.0 C`

The running C# telemetry consumer processed the Event Hubs record and emitted a maintenance command.

The command was then received using the listen-only Service Bus credential and validated successfully:

- `schemaVersion`: `1.0`
- `ruleId`: `OVERHEAT`
- `eventId`: `p5-live-overheat-001`
- `machineId`: `P5-LIVE-CNC-0001`
- `sequence`: `1`
- `severity`: `Critical`
- `action`: `InspectCoolingSystem`

This establishes the P5 rule-to-command flow using live Azure services rather than a mocked transport.

## Security evidence

The telemetry consumer used a queue authorization rule with only `Send`.

The validation receiver used a separate queue authorization rule with only `Listen`.

No connection strings or keys are committed to the repository.

## Teardown

After validation:

- the telemetry consumer was stopped;
- runtime secrets were cleared from the shell;
- Terraform destroy completed;
- `terraform state list` returned no resources;
- Azure reported that the resource group no longer existed.

The P5 Azure environment therefore does not remain deployed after evidence collection.

## Known consistency limitation

The Cosmos DB state update and Service Bus publication are not atomic.

State currently advances before command publication. If the state write succeeds and the Service Bus send subsequently fails, Event Hubs does not checkpoint the record. A later redelivery can nevertheless see the already-advanced sequence and suppress regeneration of the command.

P5 therefore does not claim exactly-once processing or atomic state-and-command persistence.

A transactional-outbox or equivalent command-intent mechanism is a future hardening option.

## P6 boundary

P5 provisions Service Bus delivery-count and dead-letter-related queue settings, but it does not yet implement or demonstrate the complete poison-message -> DLQ -> inspection -> re-drive workflow.

That work remains P6.
