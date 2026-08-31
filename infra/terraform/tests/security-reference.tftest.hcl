mock_provider "azurerm" {}

run "security_reference_disabled_by_default" {
  command = plan

  assert {
    condition     = var.security_reference_enabled == false
    error_message = "P11 security reference mode must remain disabled by default for low-cost development deployments."
  }

  assert {
    condition     = length(azurerm_virtual_network.security_reference) == 0
    error_message = "The P11 reference VNet must not be created in the default development configuration."
  }

  assert {
    condition     = length(azurerm_private_endpoint.event_hubs) == 0
    error_message = "Private endpoints must not be created unless security reference mode is explicitly enabled."
  }

  assert {
    condition     = length(azurerm_user_assigned_identity.api_runtime) == 0
    error_message = "P11 managed identities must not add resources to the default development deployment."
  }
}

run "security_reference_models_private_access" {
  command = plan

  variables {
    security_reference_enabled = true
  }

  assert {
    condition     = length(azurerm_virtual_network.security_reference) == 1
    error_message = "Security reference mode must model a private-reference VNet."
  }

  assert {
    condition     = length(azurerm_subnet.private_endpoints) == 1 && length(azurerm_subnet.container_apps) == 1
    error_message = "Security reference mode must separate private endpoints from the Container Apps integration subnet."
  }

  assert {
    condition     = length(azurerm_user_assigned_identity.api_runtime) == 1 && length(azurerm_user_assigned_identity.consumer_runtime) == 1
    error_message = "API and telemetry consumer workloads must use distinct managed identities."
  }

  assert {
    condition     = azurerm_role_assignment.api_acr_pull[0].role_definition_name == "AcrPull"
    error_message = "The API runtime identity must use AcrPull rather than ACR administrative credentials."
  }

  assert {
    condition     = azurerm_role_assignment.consumer_eventhub_receiver[0].role_definition_name == "Azure Event Hubs Data Receiver"
    error_message = "The telemetry consumer identity must have Event Hubs receiver access."
  }

  assert {
    condition     = azurerm_role_assignment.consumer_servicebus_sender[0].role_definition_name == "Azure Service Bus Data Sender"
    error_message = "The telemetry consumer identity must have least-privilege Service Bus sender access."
  }

  assert {
    condition     = azurerm_role_assignment.consumer_checkpoint_blob[0].role_definition_name == "Storage Blob Data Contributor"
    error_message = "The telemetry consumer identity must have Blob data access for checkpoint persistence."
  }
  assert {
    condition     = length(azurerm_cosmosdb_sql_role_assignment.api_machine_state_reader) == 1
    error_message = "Security reference mode must model Cosmos DB read access for the API identity."
  }
  assert {
    condition     = length(azurerm_cosmosdb_sql_role_assignment.consumer_machine_state_contributor) == 1
    error_message = "Security reference mode must model Cosmos DB contributor access for the consumer identity."
  }

  assert {
    condition = alltrue([
      length(azurerm_private_endpoint.event_hubs) == 1,
      length(azurerm_private_endpoint.service_bus) == 1,
      length(azurerm_private_endpoint.cosmos) == 1,
      length(azurerm_private_endpoint.checkpoints) == 1,
      length(azurerm_private_endpoint.telemetry_cold) == 1
    ])
    error_message = "Security reference mode must model private endpoints for messaging, state, checkpoints, and capture storage."
  }

  assert {
    condition = alltrue([
      contains(keys(azurerm_private_dns_zone.security_reference), "servicebus"),
      contains(keys(azurerm_private_dns_zone.security_reference), "blob"),
      contains(keys(azurerm_private_dns_zone.security_reference), "cosmos")
    ])
    error_message = "Security reference mode must model the required private DNS zones."
  }
}
