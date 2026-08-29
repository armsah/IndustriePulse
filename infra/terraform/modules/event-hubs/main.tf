resource "azurerm_eventhub_namespace" "this" {
  name                = var.namespace_name
  location            = var.location
  resource_group_name = var.resource_group_name

  sku      = "Standard"
  capacity = var.capacity

  auto_inflate_enabled          = false
  local_authentication_enabled  = true
  public_network_access_enabled = true
  minimum_tls_version           = "1.2"

  tags = var.tags
}

resource "azurerm_eventhub" "telemetry" {
  name              = var.eventhub_name
  namespace_id      = azurerm_eventhub_namespace.this.id
  partition_count   = var.partition_count
  message_retention = var.retention_days
}

resource "azurerm_eventhub_authorization_rule" "producer" {
  name                = "telemetry-producer"
  eventhub_name       = azurerm_eventhub.telemetry.name
  namespace_name      = azurerm_eventhub_namespace.this.name
  resource_group_name = var.resource_group_name

  listen = false
  send   = true
  manage = false
}

resource "azurerm_eventhub_authorization_rule" "consumer" {
  name                = "telemetry-consumer"
  namespace_name      = azurerm_eventhub_namespace.this.name
  eventhub_name       = azurerm_eventhub.telemetry.name
  resource_group_name = var.resource_group_name

  listen = true
  send   = false
  manage = false
}

resource "azurerm_eventhub_consumer_group" "telemetry_processor" {
  name                = "telemetry-processor"
  namespace_name      = azurerm_eventhub_namespace.this.name
  eventhub_name       = azurerm_eventhub.telemetry.name
  resource_group_name = var.resource_group_name
}
