locals {
  project = "industriepulse"

  # Event Hubs namespace names must be globally unique.
  # A stable fragment of the active subscription ID avoids requiring
  # a random provider or committing user-specific values to the repository.
  subscription_suffix = substr(
    replace(data.azurerm_client_config.current.subscription_id, "-", ""),
    0,
    8
  )

  resource_group_name = "rg-${local.project}-${var.environment}-weu"
  namespace_name      = "ehns-${local.project}-${var.environment}-${local.subscription_suffix}"
  telemetry_hub_name  = "telemetry"

  common_tags = {
    project     = "IndustriePulse"
    environment = var.environment
    managed_by  = "Terraform"
    phase       = "P2"
  }
}

resource "azurerm_resource_group" "main" {
  name     = local.resource_group_name
  location = var.location

  tags = local.common_tags
}

resource "azurerm_eventhub_namespace" "telemetry" {
  name                = local.namespace_name
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  sku      = "Standard"
  capacity = var.eventhub_capacity

  auto_inflate_enabled          = false
  local_authentication_enabled  = true
  public_network_access_enabled = true
  minimum_tls_version           = "1.2"

  tags = local.common_tags
}

resource "azurerm_eventhub" "telemetry" {
  name              = local.telemetry_hub_name
  namespace_id      = azurerm_eventhub_namespace.telemetry.id
  partition_count   = var.telemetry_partition_count
  message_retention = var.telemetry_retention_days
}

resource "azurerm_eventhub_authorization_rule" "telemetry_producer" {
  name                = "telemetry-producer"
  eventhub_name       = azurerm_eventhub.telemetry.name
  namespace_name      = azurerm_eventhub_namespace.telemetry.name
  resource_group_name = azurerm_resource_group.main.name

  listen = false
  send   = true
  manage = false
}
