# IndustriePulse Security Access Paths

**Phase:** P11

This document defines the intended production-reference authentication, authorization, and network path for each IndustriePulse workload.

## Access-path matrix

| Source | Destination | Authentication | Authorization | Production network path |
| --- | --- | --- | --- | --- |
| Telemetry producer | Event Hubs telemetry hub | Microsoft Entra workload identity | Azure Event Hubs Data Sender | Approved factory/application network to Event Hubs private endpoint |
| Telemetry consumer | Event Hubs telemetry hub | Managed identity | Azure Event Hubs Data Receiver | Container workload VNet to Event Hubs private endpoint |
| Telemetry consumer | Checkpoint Blob Storage | Managed identity | Storage Blob Data Contributor | Container workload VNet to Blob private endpoint |
| Telemetry consumer | Cosmos DB machine state | Managed identity | Cosmos DB Built-in Data Contributor | Container workload VNet to Cosmos DB private endpoint |
| Telemetry consumer | Service Bus maintenance queue | Managed identity | Azure Service Bus Data Sender | Container workload VNet to Service Bus private endpoint |
| API runtime | Cosmos DB machine state | Managed identity | Cosmos DB Built-in Data Reader | Container Apps VNet to Cosmos DB private endpoint |
| API runtime | Azure Container Registry | Managed identity | AcrPull | Public registry endpoint in low-cost reference; private registry networking is a stricter production option |
| Event Hubs Capture service | Telemetry capture Blob Storage | Azure service integration | Azure-managed capture authorization | Azure service path to capture storage; private endpoint provided for workload/replay access |
| Replay worker/operator | Capture Blob Storage | Entra identity / managed identity | Scoped Blob data role | Approved network to Blob private endpoint |
| Replay worker/operator | Replay Event Hub | Entra identity / managed identity | Scoped Event Hubs sender role | Approved network to Event Hubs private endpoint |
| Operations/re-drive tool | Service Bus queue and DLQ | Entra operator/workload identity | Sender/Receiver roles only as required | Approved administrative network to Service Bus private endpoint |
| Azure administrator / Terraform | Azure Resource Manager | Entra identity | Control-plane RBAC | Azure management endpoint |

## Private DNS paths

| Azure service | Private DNS zone |
| --- | --- |
| Event Hubs | `privatelink.servicebus.windows.net` |
| Service Bus | `privatelink.servicebus.windows.net` |
| Blob Storage | `privatelink.blob.core.windows.net` |
| Cosmos DB for NoSQL | `privatelink.documents.azure.com` |

The P11 VNet links these zones to the private-reference network so Azure service hostnames resolve to private endpoint addresses for VNet-connected workloads.

## Identity boundaries

### API identity

The API receives only the permissions it requires:

- AcrPull on the API container registry;
- Cosmos DB Built-in Data Reader for machine-state queries.

The API does not require Event Hubs receiver rights, Service Bus sender rights, or Blob checkpoint contributor rights.

### Telemetry consumer identity

The consumer receives:

- Azure Event Hubs Data Receiver on the telemetry Event Hub;
- Storage Blob Data Contributor for checkpoint persistence;
- Cosmos DB Built-in Data Contributor for monotonic machine-state updates;
- Azure Service Bus Data Sender for maintenance commands.

The consumer does not receive ACR administrative credentials or broad Service Bus management access.

### Operational identities

DLQ inspection and re-drive should use separate human or automation identities with only the Service Bus sender/receiver permissions required by the runbook. Production operators should not reuse the application managed identities.

## Development versus production-reference path

| Concern | Current dev path | Production-reference target |
| --- | --- | --- |
| Event Hubs auth | Scoped SAS authorization rules | Entra identity + Event Hubs RBAC |
| Service Bus auth | Scoped SAS authorization rules | Entra identity + Service Bus RBAC |
| Cosmos API auth | Connection string | Managed identity + Cosmos data-plane RBAC |
| Checkpoint Blob auth | Connection string | Managed identity + Blob data RBAC |
| ACR pull | Admin username/password | Managed identity + AcrPull |
| PaaS network | Public endpoints | Private Link + private DNS |
| Container Apps ingress | Public HTTPS for demo | Public or private ingress according to product requirements, protected by application authentication |
| Local authentication | Enabled for development | Disabled after Entra migration where supported |

## Migration order

1. Create workload identities.
2. Assign least-privilege RBAC.
3. Update applications to use Entra credentials instead of secrets.
4. Establish VNet integration, private endpoints, and private DNS.
5. Validate each private data path.
6. Disable public network access on protected PaaS services.
7. Disable local/key-based authentication where supported.
8. Remove obsolete connection strings, SAS policies, and ACR administrative credentials.

This order avoids locking workloads out before their replacement identity and network paths are proven.

## Exit criterion

**P11 exit criterion: access paths documented - PASS.**
