# ADR-014: Entra Identity and Private Connectivity Reference Architecture

- Status: Accepted
- Date: 2026-08-31
- Phase: P11

## Context

Earlier IndustriePulse phases intentionally optimized Azure deployments for inexpensive, short-lived portfolio demonstrations. The development configuration therefore uses scoped connection strings or SAS authorization rules for several services, ACR administrative credentials, and public Azure PaaS endpoints.

Those choices are useful for development but are not the intended production security boundary.

P11 requires a security/private-reference design focused on Microsoft Entra ID and Azure Private Link, with a threat model and explicit access paths.

## Decision

IndustriePulse maintains two clearly distinguished security profiles.

### Development profile

The existing inexpensive development topology remains the default. `security_reference_enabled` defaults to false so normal Terraform plans do not incur private networking resources or alter previously demonstrated workflows.

### Production-reference profile

When explicitly enabled, Terraform models:

- a dedicated private-reference VNet;
- a private-endpoint subnet;
- a delegated Container Apps subnet;
- private DNS zones for Service Bus/Event Hubs, Blob Storage, and Cosmos DB;
- Event Hubs, Service Bus, Cosmos DB, checkpoint Blob, and telemetry-capture Blob private endpoints;
- separate API and telemetry-consumer managed identities;
- AcrPull for the API runtime;
- Event Hubs receiver, Service Bus sender, and Blob contributor RBAC for the consumer;
- Cosmos DB data-plane Reader for the API;
- Cosmos DB data-plane Contributor for the consumer.

After application authentication is migrated to Entra ID and private connectivity is proven, a production deployment should disable local authentication and public data-plane access where supported.

## Why separate identities

Using separate API and consumer identities avoids a shared workload principal becoming a privilege aggregation point. The API needs read access to machine state and image-pull access. The consumer needs telemetry receive, checkpoint write, state write, and maintenance-command send privileges.

## Why Private Link

Private Link provides private IP-based access to supported Azure PaaS data planes. Combined with private DNS and disabled public network access, it removes production workload dependence on public service endpoints.

A private endpoint by itself is not considered sufficient isolation: public network access must also be disabled after workload migration.

## ACR decision

The existing registry remains on the inexpensive development tier. The production-reference identity model uses managed identity with AcrPull instead of registry administrative credentials.

Private registry networking is documented as a stricter production option rather than part of the default low-cost development resources.

## Consequences

### Positive

- application secrets can be removed from production workload configuration;
- permissions become workload-specific and auditable;
- core data-plane services have documented private network paths;
- development cost remains unchanged unless reference mode is explicitly enabled;
- security architecture is testable through Terraform without provisioning Azure resources.

### Negative

- private networking adds DNS and routing complexity;
- managed identity migration requires application code/configuration changes;
- disabling public/local access must be sequenced carefully to avoid outages;
- stricter private registry networking can require a more expensive registry tier;
- private endpoints introduce additional Azure resources and cost.

## Alternatives considered

### Replace all development authentication immediately

Rejected because it would unnecessarily destabilize previously proven phases and make short-lived portfolio demonstrations more expensive and harder to reproduce.

### Keep connection strings and rely only on network isolation

Rejected because leaked shared credentials remain valuable and do not provide workload-specific least privilege.

### Use managed identity but keep all PaaS endpoints public

Insufficient for the production-reference goal because identity hardening does not remove the public network attack surface.

### Enable every private endpoint in normal development

Rejected because P11 is a reference-design phase and the additional recurring resources are unnecessary for everyday local development.

## Related documents

- [Threat model](../security/threat-model.md)
- [Security access paths](../security/access-paths.md)
