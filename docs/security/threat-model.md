# IndustriePulse Threat Model

**Phase:** P11

**Scope:** Telemetry ingestion, stream processing, machine-state persistence, maintenance messaging, cold capture/replay, API/UI hosting, container image delivery, and operational access.

## Security objectives

- prevent unauthorized telemetry publication and consumption;
- prevent unauthorized machine-state reads or writes;
- prevent unauthorized maintenance-command publication, consumption, or re-drive;
- prevent disclosure of Azure credentials, connection strings, keys, or tokens;
- constrain application access using workload identity and least-privilege RBAC;
- restrict production data-plane traffic to approved private access paths;
- preserve availability and replayability without granting unnecessarily broad privileges;
- retain observable and auditable control-plane and data-plane access.

## Assets

| Asset | Security concern |
| --- | --- |
| Live machine telemetry | Integrity, confidentiality, availability |
| Event Hubs checkpoints | Integrity and availability |
| Current machine state | Integrity and confidentiality |
| Maintenance commands | Integrity, authorization, availability |
| Dead-letter messages | Confidentiality and controlled recovery |
| Captured telemetry | Confidentiality, integrity, retention |
| Container images | Supply-chain integrity |
| Azure identities and RBAC | Privilege control |
| Monitoring data | Operational confidentiality and integrity |
| Infrastructure state/configuration | Sensitive metadata and privilege boundary |

## Trust boundaries

1. Factory or simulator producer to Azure ingestion.
2. Azure Event Hubs to the telemetry consumer.
3. Consumer workload to checkpoint Blob Storage.
4. Consumer workload to Cosmos DB.
5. Consumer workload to Service Bus.
6. API runtime to Cosmos DB.
7. Container Apps runtime to Azure Container Registry.
8. Azure workloads to Private Link endpoints and private DNS.
9. Human operator or CI/CD identity to the Azure control plane.

## Threat analysis

| STRIDE category | Example threat | Primary mitigation | Residual risk |
| --- | --- | --- | --- |
| Spoofing | Attacker publishes telemetry as a legitimate producer | Microsoft Entra workload identity, scoped Event Hubs Data Sender role, TLS | Compromised producer identity can still send until revoked |
| Spoofing | Workload impersonates the API or consumer | Separate managed identities per workload | Identity compromise remains possible |
| Tampering | Unauthorized machine-state mutation | Cosmos DB data-plane RBAC; consumer gets contributor, API gets reader | Authorized consumer bugs can still write bad state |
| Tampering | Maintenance command modification or injection | Service Bus Data Sender scoped to intended workload; deterministic command identity | Legitimate sender compromise remains impactful |
| Tampering | Checkpoint manipulation causes skipped or replayed work | Blob data RBAC scoped to consumer identity | Consumer compromise can alter its own checkpoints |
| Repudiation | Operator denies security-sensitive control-plane action | Entra authentication plus Azure Activity Log/Azure Monitor | Log retention and review procedures remain operational responsibilities |
| Information disclosure | Connection strings or SAS keys leak from configuration | Managed identity removes stored application credentials in the production-reference path | Development mode still uses connection strings for low-cost demonstrations |
| Information disclosure | Public PaaS endpoints expose attack surface | Private Link, private DNS, and disabling public network access after migration | Misconfigured DNS or network policies can break or weaken isolation |
| Information disclosure | Captured telemetry accessed by unauthorized workload | Private Blob container, data-plane RBAC, Private Link | Storage administrators remain privileged |
| Denial of service | Unauthorized or excessive Event Hubs traffic | Entra authorization, quotas, monitoring, partition/capacity planning | Authorized producer overload remains possible |
| Denial of service | Private DNS or endpoint failure blocks workloads | Explicit DNS topology, monitoring, infrastructure-as-code recovery | Private networking introduces additional dependencies |
| Elevation of privilege | Shared broad credentials grant more access than required | Resource-scoped RBAC and separate managed identities | Azure administrators retain control-plane privilege |
| Elevation of privilege | ACR admin credential permits broad registry access | Disable admin credentials after migration; use managed identity plus AcrPull | Basic-tier dev mode retains admin credentials |

## Development-mode risks accepted

The existing low-cost development deployment intentionally retains several simplifications:

- Event Hubs local authentication and public network access are enabled;
- Service Bus local authentication and public network access are enabled;
- checkpoint and capture Storage accounts permit public network access;
- Cosmos DB permits public network access and the P8 API uses a connection string;
- ACR Basic has administrative credentials enabled;
- Container Apps ingress is public.

These are explicitly development conveniences and are not represented as the production target.

## Production-reference controls

The P11 reference design adds:

- separate managed identities for API and telemetry-consumer workloads;
- least-privilege Azure RBAC for Event Hubs, Service Bus, Blob Storage, and ACR;
- Cosmos DB data-plane RBAC;
- a dedicated virtual network;
- separate Container Apps and private-endpoint subnets;
- Private Link endpoints for Event Hubs, Service Bus, Cosmos DB, checkpoint storage, and telemetry capture storage;
- private DNS zones and VNet links for Azure PaaS name resolution.

After all workloads have migrated successfully to Entra-based authentication and private networking, the production implementation should disable local authentication and public PaaS data-plane access where supported.

## ACR network-isolation tradeoff

The project uses ACR Basic to preserve low development cost. The production-reference identity path replaces registry administrative credentials with managed identity and AcrPull. Full ACR Private Link isolation requires upgrading the registry tier and is therefore documented as a stricter production control rather than enabled in the low-cost development deployment.

## Out of scope

- corporate Entra Conditional Access policy design;
- end-user authorization and tenant federation;
- enterprise firewall products or SIEM operations;
- certificate lifecycle for physical factory devices;
- full CI/CD supply-chain signing and provenance;
- production incident-response organization and staffing.

## P11 conclusion

The security model separates low-cost development shortcuts from the intended production trust model. Production workloads authenticate with Entra identities, receive only required data-plane roles, and communicate with core Azure data services through documented private access paths.
