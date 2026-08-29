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
