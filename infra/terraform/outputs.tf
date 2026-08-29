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
