output "resource_group_name" {
  description = "Resource group containing the P2 Event Hubs infrastructure."
  value       = azurerm_resource_group.main.name
}

output "eventhub_namespace_name" {
  description = "IndustriePulse Event Hubs namespace name."
  value       = module.event_hubs.namespace_name
}

output "telemetry_eventhub_name" {
  description = "Live telemetry Event Hub name."
  value       = module.event_hubs.eventhub_name
}

output "telemetry_partition_count" {
  description = "Configured telemetry Event Hub partition count."
  value       = module.event_hubs.partition_count
}

output "eventhub_capacity" {
  description = "Configured Standard throughput-unit capacity."
  value       = module.event_hubs.capacity
}

output "telemetry_consumer_group_name" {
  description = "Consumer group used by the telemetry processor."
  value       = module.event_hubs.consumer_group_name
}

output "checkpoint_storage_account_name" {
  description = "Storage account used for Event Hubs processor ownership and checkpoints."
  value       = azurerm_storage_account.checkpoints.name
}

output "checkpoint_container_name" {
  description = "Blob container used for Event Hubs processor ownership and checkpoints."
  value       = azurerm_storage_container.checkpoints.name
}

output "telemetry_consumer_authorization_rule_name" {
  description = "Listen-only Event Hubs authorization rule for the P3 consumer."
  value       = module.event_hubs.consumer_authorization_rule_name
}

output "cosmos_account_name" {
  description = "Cosmos DB account used for the P4 machine current-state projection."
  value       = azurerm_cosmosdb_account.machine_state.name
}

output "cosmos_database_name" {
  description = "Cosmos DB SQL database containing IndustriePulse machine state."
  value       = azurerm_cosmosdb_sql_database.machine_state.name
}

output "cosmos_machine_state_container_name" {
  description = "Cosmos DB container storing current state by machineId."
  value       = azurerm_cosmosdb_sql_container.machine_state.name
}

output "servicebus_namespace_name" {
  description = "Service Bus namespace used for P5 maintenance messaging."
  value       = azurerm_servicebus_namespace.maintenance.name
}

output "maintenance_commands_queue_name" {
  description = "Service Bus queue receiving maintenance commands."
  value       = azurerm_servicebus_queue.maintenance_commands.name
}

output "maintenance_sender_authorization_rule_name" {
  description = "Send-only authorization rule used by the telemetry processor."
  value       = azurerm_servicebus_queue_authorization_rule.maintenance_sender.name
}

output "maintenance_receiver_authorization_rule_name" {
  description = "Listen-only authorization rule used for P5 maintenance command validation."
  value       = azurerm_servicebus_queue_authorization_rule.maintenance_receiver.name
}

output "maintenance_operations_authorization_rule_name" {
  description = "Send-and-listen authorization rule used by P6 maintenance operations tooling."
  value       = azurerm_servicebus_queue_authorization_rule.maintenance_operations.name
}
output "telemetry_capture_storage_account_name" {
  description = "Storage account receiving captured telemetry."
  value       = azurerm_storage_account.telemetry_cold.name
}

output "telemetry_capture_container_name" {
  description = "Private Blob container receiving Event Hubs Capture files."
  value       = azurerm_storage_container.telemetry_capture.name
}

output "telemetry_replay_eventhub_name" {
  description = "Isolated Event Hub used for historical telemetry replay."
  value       = azurerm_eventhub.telemetry_replay.name
}

output "replay_consumer_group_name" {
  description = "Consumer group used to validate historical replay."
  value       = azurerm_eventhub_consumer_group.replay_processor.name
}

output "replay_sender_authorization_rule_name" {
  description = "Send-only authorization rule used by the replay job."
  value       = azurerm_eventhub_authorization_rule.replay_sender.name
}

output "replay_receiver_authorization_rule_name" {
  description = "Listen-only authorization rule used by replay validation."
  value       = azurerm_eventhub_authorization_rule.replay_receiver.name
}

output "container_registry_name" {
  description = "Azure Container Registry holding the P8 API/UI image."
  value       = azurerm_container_registry.api.name
}

output "container_registry_login_server" {
  description = "Login server for the P8 Azure Container Registry."
  value       = azurerm_container_registry.api.login_server
}

output "container_app_environment_name" {
  description = "Container Apps environment hosting the P8 API/UI."
  value       = azurerm_container_app_environment.api.name
}

output "api_container_app_name" {
  description = "P8 Container App serving the IndustriePulse API and dashboard."
  value       = azurerm_container_app.api.name
}

output "api_container_app_fqdn" {
  description = "Public HTTPS hostname for the P8 IndustriePulse API/UI."
  value       = azurerm_container_app.api.ingress[0].fqdn
}

output "log_analytics_workspace_name" {
  description = "P9 Log Analytics workspace name."
  value       = azurerm_log_analytics_workspace.observability.name
}

output "application_insights_name" {
  description = "P9 Application Insights component name."
  value       = azurerm_application_insights.consumer.name
}

output "observability_workbook_id" {
  description = "P9 Azure Monitor Workbook resource ID."
  value       = azurerm_application_insights_workbook.consumer_observability.id
}