output "namespace_name" {
  description = "Event Hubs namespace name."
  value       = azurerm_eventhub_namespace.this.name
}

output "namespace_id" {
  description = "Event Hubs namespace resource ID."
  value       = azurerm_eventhub_namespace.this.id
}

output "eventhub_name" {
  description = "Telemetry Event Hub name."
  value       = azurerm_eventhub.telemetry.name
}

output "eventhub_id" {
  description = "Telemetry Event Hub resource ID."
  value       = azurerm_eventhub.telemetry.id
}

output "partition_count" {
  description = "Configured telemetry partition count."
  value       = azurerm_eventhub.telemetry.partition_count
}

output "capacity" {
  description = "Configured Standard throughput-unit capacity."
  value       = azurerm_eventhub_namespace.this.capacity
}

output "producer_authorization_rule_name" {
  description = "Name of the send-only producer authorization rule."
  value       = azurerm_eventhub_authorization_rule.producer.name
}

output "consumer_group_name" {
  description = "Consumer group used by the telemetry processor."
  value       = azurerm_eventhub_consumer_group.telemetry_processor.name
}

output "consumer_authorization_rule_name" {
  description = "Listen-only authorization rule used by the telemetry consumer."
  value       = azurerm_eventhub_authorization_rule.consumer.name
}
