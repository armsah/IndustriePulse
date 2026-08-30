# ADR-011: Deploy the API and Dashboard with Azure Container Apps

- Status: Accepted
- Phase: P8
- Decision date: 2026-08-30

## Context

IndustriePulse needs a deployable HTTP surface for querying current machine state and presenting a lightweight operator dashboard.

The application already exposes the current-state API backed by Azure Cosmos DB. P8 requires an Azure deployment model that is appropriate for a portfolio/demo environment while remaining representative of a production-oriented container platform.

The workload is intermittent in development. Keeping an application replica continuously allocated would provide little value during periods with no demo traffic.

## Decision

Deploy the ASP.NET Core API and static dashboard as a single containerized application on Azure Container Apps.

The deployment uses:

- an ASP.NET Core .NET 10 application;
- static dashboard assets served from `wwwroot`;
- external HTTPS ingress;
- target port `8080`;
- Azure Container Registry Basic for the application image;
- a single active Container Apps revision;
- `0.25` vCPU and `0.5 GiB` memory per replica;
- minimum replicas `0`;
- maximum replicas `3`;
- `/health` as the liveness and readiness endpoint;
- Cosmos DB configuration supplied to the container through environment configuration and an Azure Container Apps secret.

The development environment uses Container Apps consumption-oriented serverless compute so that the API is eligible to scale to zero when idle.

## Rationale

### One API/UI container

The dashboard is intentionally small and consumes the same API exposed by the backend. Serving the static files from ASP.NET Core avoids introducing a separate frontend deployment, CDN, storage website, or additional networking boundary during P8.

This keeps the deployment architecture proportional to the project while preserving a clear API boundary.

### Azure Container Apps

Container Apps provides managed container execution, HTTPS ingress, revision management, probes, and horizontal scaling without requiring a Kubernetes cluster to be operated directly.

It is appropriate for the intermittent development/demo workload because an HTTP application can scale to zero.

### Scale limits

The Terraform configuration sets:

- `min_replicas = 0`
- `max_replicas = 3`

The zero minimum permits scale-to-zero behavior during idle periods. The maximum of three limits accidental development scale-out while still demonstrating horizontal scaling configuration.

During live verification, Terraform state reported the configured minimum as `0` and maximum as `3`. The Azure CLI representation omitted the zero-valued minimum and returned `null`; Azure documents `0` as the default HTTP minimum replica count.

### Development economics

Scale-to-zero reduces the compute cost of the Container App itself when no replicas are running.

This does **not** make the complete IndustriePulse Azure environment free. Azure Container Registry, Cosmos DB activity, Event Hubs, Service Bus, storage, logging, network features, request charges, or other dependent services can still incur charges.

For that reason, P8 live infrastructure is deployed only long enough to collect deployment evidence and is then destroyed.

### Registry authentication

P8 enables the Azure Container Registry administrative credentials and supplies them to the Container App as a secret.

This is deliberately a development simplification rather than the target production security design. A production deployment should use workload/managed identity with an appropriate `AcrPull` role and eliminate registry administrator credentials.

Security hardening belongs to P11.

## Consequences

### Positive

- API and dashboard share one deployable artifact.
- The same Docker image can be built locally and in Azure Container Registry.
- HTTPS ingress is managed by Azure Container Apps.
- Health probes provide an explicit platform health contract.
- Development replicas can scale to zero.
- Maximum replica count constrains development scale-out.
- Terraform defines the runtime configuration reproducibly.

### Trade-offs

- A request after scale-to-zero can experience cold-start latency.
- The API and dashboard currently scale as one unit.
- P8 registry authentication uses ACR administrative credentials.
- The full application remains dependent on Cosmos DB and therefore scale-to-zero does not imply zero total platform cost.
- Terraform state contains sensitive infrastructure values and must remain protected and uncommitted.

## Validation

P8 validation demonstrated:

- Terraform tests: `5 passed, 0 failed`;
- .NET tests: `26 passed, 0 failed`;
- successful local production Docker build;
- successful image build/push to Azure Container Registry;
- successful Azure Container Apps provisioning;
- live `/health` response reporting `healthy`;
- live dashboard returning HTTP `200`;
- dashboard HTML containing the IndustriePulse title and Machine State interface;
- Terraform state reporting `min_replicas = 0` and `max_replicas = 3`;
- successful Cosmos-backed query for deterministic machine `P8-DEMO-CNC-0001`.

## Follow-up

P9 adds production-oriented observability.

P11 revisits registry and application authentication, secret handling, managed identities, and private-network reference architecture.
