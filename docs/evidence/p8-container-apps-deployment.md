# P8 Evidence: Azure Container Apps API/UI Deployment

## Objective

P8 adds a deployable API and dashboard using Azure Container Apps and documents the development scale-to-zero economics.

Exit criteria:

- Container Apps API/UI deployment defined as infrastructure as code;
- deployment demonstrated in Azure;
- API/UI reachable through Container Apps ingress;
- current machine state query works against the deployed application;
- scale-to-zero development configuration and economics documented.

## Local Validation

Before Azure deployment, the implementation passed all local validation gates.

### Terraform

```text
Success! 5 passed, 0 failed.
```

The P8 Container Apps test verifies:

- Azure Container Registry Basic SKU;
- single-revision mode;
- external ingress;
- target port `8080`;
- minimum replicas `0`;
- maximum replicas `3`;
- container CPU `0.25`;
- container memory `0.5Gi`.

### .NET

```text
Test summary: total: 26, failed: 0, succeeded: 26, skipped: 0
```

The API test suite includes verification of the `/health` endpoint.

### Container Build

The production Dockerfile built successfully with Docker Desktop using the image tag:

```text
industriepulse-api:p8
```

The final image uses the .NET 10 ASP.NET runtime and listens on port `8080`.

## Azure Deployment Procedure

Azure Container Registry was bootstrapped first because the Container App references an image stored in that registry.

Terraform resource targeting was used only for this bootstrap dependency. It created:

- the development resource group;
- the Basic Azure Container Registry.

The application image was then built and pushed to ACR.

A subsequent normal Terraform apply reconciled the complete configuration and created the remaining resources.

The full apply completed successfully:

```text
Apply complete! Resources: 23 added, 0 changed, 0 destroyed.
```

The Container App provisioning state was:

```text
Succeeded
```

The deployed image used the expected tag:

```text
industriepulse-api:p8
```

## Scale Configuration

Terraform state reported:

```text
max_replicas = 3
min_replicas = 0
```

The Azure CLI resource representation reported the configured maximum while omitting the zero-valued minimum:

```json
{
  "cooldownPeriod": 300,
  "maxReplicas": 3,
  "minReplicas": null,
  "pollingInterval": 30,
  "rules": null
}
```

This difference is recorded rather than interpreting the CLI `null` value as a non-zero minimum. Azure Container Apps documents zero as the default minimum replica count for HTTP scaling.

The deployment is therefore eligible for scale-to-zero.

The maximum of three replicas also bounds accidental development scale-out while retaining an explicit horizontal scaling configuration.

## Live Health Verification

The deployed Container App health endpoint returned:

```json
{
  "status": "healthy"
}
```

This verifies that the ASP.NET Core container was running behind Azure Container Apps ingress and responding through its public HTTPS endpoint.

## Live Dashboard Verification

The deployed root page was retrieved over HTTPS using basic HTML parsing.

Results:

```text
UI_STATUS=200
UI_HAS_TITLE=True
UI_HAS_MACHINE_STATE=True
```

This verifies that the same Container App successfully serves the static IndustriePulse dashboard.

## Cosmos-Backed API Verification

A deterministic document was inserted directly into the P8 Cosmos DB container solely for deployment verification.

The test machine was:

```text
P8-DEMO-CNC-0001
```

A request through the public Container Apps API returned:

```text
machineId    : P8-DEMO-CNC-0001
siteId       : SITE-P8
machineType  : CNC
temperatureC : 61.5
vibrationMmS : 2.3
sequence     : 1
```

The verified request path was:

```text
HTTPS client
    |
    v
Azure Container Apps ingress
    |
    v
IndustriePulse.Api container
    |
    v
Cosmos DB machine-state container
```

This demonstrates that the deployed API can execute the P4 current-state query through the P8 Container Apps runtime.

## Development Economics

The Container App uses a zero minimum replica setting, allowing the application to scale to zero when idle.

When a Container Apps revision has zero running replicas, no Container Apps resource-consumption charge is incurred for those replicas. Request charges and applicable Azure grants remain governed by the Container Apps billing model.

This claim is deliberately limited to Container Apps compute. Scale-to-zero does not make the complete IndustriePulse Azure environment free.

Other resources can incur charges independently, including:

- Azure Container Registry;
- Event Hubs;
- Service Bus;
- Cosmos DB;
- Storage;
- monitoring services;
- networking services.

Cold-start latency after an idle scale-to-zero period is accepted for this development and portfolio workload.

Consequently, the live P8 environment was kept short-lived and destroyed after deployment evidence was collected.

## Security Note

The P8 deployment uses Azure Container Registry administrative credentials as a Container Apps secret to keep this phase focused on container deployment mechanics.

The Cosmos DB connection string is likewise supplied to the application through Container Apps secret configuration.

These are development simplifications and are not the intended production authentication model.

P11 will address:

- managed identity;
- `AcrPull` role-based access;
- improved application secret handling;
- private-network reference architecture.

Terraform state can contain sensitive infrastructure values and is therefore treated as sensitive and is not committed.

## Teardown Verification

The short-lived Azure environment was destroyed after deployment evidence was collected.

The initial Terraform destroy exposed an Event Hubs Capture lifecycle edge case. The Capture storage destination was removed before Terraform attempted to delete an Event Hub authorization rule. Azure rejected that child-resource deletion while validating the now-invalid Capture Blob destination.

The deployed Event Hub was confirmed to have Capture disabled:

```text
captureEnabled : false
status         : Active
```

Because Azure continued validating the stale Capture destination when the authorization rule was deleted independently, the affected Event Hub was removed directly through Azure CLI.

Terraform subsequently refreshed the out-of-band deletion and completed destruction of the remaining managed infrastructure.

Final verification reported:

```text
TERRAFORM_STATE_EMPTY=True
RESOURCE_GROUP_EXISTS=false
```

No live P8 Azure infrastructure remained after evidence collection.

### Lifecycle Hardening

The teardown exposed a genuine infrastructure dependency issue rather than an application failure.

The Terraform dependency graph was subsequently hardened so that the Event Hubs module explicitly depends on the Capture storage container.

During creation, this ensures the Capture destination exists before the Event Hubs resources that depend on it.

During destruction, Terraform reverses that dependency and removes the Event Hubs resources before removing the Capture destination.

This prevents the observed teardown sequence from recurring and makes the deployment lifecycle more reproducible.

## Result

P8 exit criteria are satisfied:

> Azure Container Apps API/UI deployment is reproducible through Terraform, the deployed health endpoint and dashboard respond over HTTPS, the deployed API successfully queries Cosmos DB current state, scale-to-zero development economics are documented, and the short-lived Azure environment was verified as fully destroyed after evidence collection.
