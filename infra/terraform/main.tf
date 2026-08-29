locals {
  project = "industriepulse"

  # Event Hubs namespace names must be globally unique.
  # A stable subscription fragment avoids committing account-specific
  # identifiers while keeping the development namespace reproducible.
  subscription_suffix = substr(
    replace(data.azurerm_client_config.current.subscription_id, "-", ""),
    0,
    8
  )

  resource_group_name     = "rg-${local.project}-${var.environment}-weu"
  namespace_name          = "ehns-${local.project}-${var.environment}-${local.subscription_suffix}"
  checkpoint_storage_name = "stip${var.environment}${local.subscription_suffix}"

  common_tags = {
    project     = "IndustriePulse"
    environment = var.environment
    managed_by  = "Terraform"
    phase       = "platform"
  }
}

resource "azurerm_resource_group" "main" {
  name     = local.resource_group_name
  location = var.location

  tags = local.common_tags
}

module "event_hubs" {
  source = "./modules/event-hubs"

  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  namespace_name      = local.namespace_name
  eventhub_name       = "telemetry"

  capacity        = var.eventhub_capacity
  partition_count = var.telemetry_partition_count
  retention_days  = var.telemetry_retention_days

  tags = local.common_tags
}

resource "azurerm_storage_account" "checkpoints" {
  name                     = local.checkpoint_storage_name
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"

  access_tier                     = "Hot"
  https_traffic_only_enabled      = true
  min_tls_version                 = "TLS1_2"
  allow_nested_items_to_be_public = false
  public_network_access_enabled   = true

  tags = merge(local.common_tags, {
    phase = "P3"
    role  = "eventhub-checkpoints"
  })
}

resource "azurerm_storage_container" "checkpoints" {
  name                  = "eventhub-checkpoints"
  storage_account_id    = azurerm_storage_account.checkpoints.id
  container_access_type = "private"
}

moved {
  from = azurerm_eventhub_namespace.telemetry
  to   = module.event_hubs.azurerm_eventhub_namespace.this
}

moved {
  from = azurerm_eventhub.telemetry
  to   = module.event_hubs.azurerm_eventhub.telemetry
}

moved {
  from = azurerm_eventhub_authorization_rule.telemetry_producer
  to   = module.event_hubs.azurerm_eventhub_authorization_rule.producer
}
