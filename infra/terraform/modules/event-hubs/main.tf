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

  dynamic "capture_description" {
    for_each = var.capture_enabled ? [1] : []

    content {
      enabled             = true
      encoding            = "Avro"
      interval_in_seconds = 60
      size_limit_in_bytes = 10485760
      skip_empty_archives = true

      destination {
        name                = "EventHubArchive.AzureBlockBlob"
        archive_name_format = "{Namespace}/{EventHub}/{PartitionId}/{Year}/{Month}/{Day}/{Hour}/{Minute}/{Second}"
        blob_container_name = var.capture_container_name
        storage_account_id  = var.capture_storage_account_id
      }
    }
  }
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
