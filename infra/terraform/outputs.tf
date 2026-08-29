output "resource_group_name" {
  description = "Resource group containing the P2 Event Hubs infrastructure."
  value       = azurerm_resource_group.main.name
}

output "eventhub_namespace_name" {
  description = "IndustriePulse Event Hubs namespace name."
  value       = azurerm_eventhub_namespace.telemetry.name
}

output "telemetry_eventhub_name" {
  description = "Live telemetry Event Hub name."
  value       = azurerm_eventhub.telemetry.name
}

output "telemetry_partition_count" {
  description = "Configured telemetry Event Hub partition count."
  value       = azurerm_eventhub.telemetry.partition_count
}

output "eventhub_capacity" {
  description = "Configured Standard throughput-unit capacity."
  value       = azurerm_eventhub_namespace.telemetry.capacity
}
