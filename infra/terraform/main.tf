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

  resource_group_name       = "rg-${local.project}-${var.environment}-weu"
  namespace_name            = "ehns-${local.project}-${var.environment}-${local.subscription_suffix}"
  checkpoint_storage_name   = "stip${var.environment}${local.subscription_suffix}"
  servicebus_namespace_name = "sbns-${local.project}-${var.environment}-${local.subscription_suffix}"

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

locals {
  cosmos_account_name = "cosmos-${local.project}-${var.environment}-${local.subscription_suffix}"
}

resource "azurerm_cosmosdb_account" "machine_state" {
  name                = local.cosmos_account_name
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  offer_type = "Standard"
  kind       = "GlobalDocumentDB"

  public_network_access_enabled = true

  capabilities {
    name = "EnableServerless"
  }

  consistency_policy {
    consistency_level = "Session"
  }

  geo_location {
    location          = azurerm_resource_group.main.location
    failover_priority = 0
    zone_redundant    = false
  }

  tags = merge(local.common_tags, {
    phase = "P4"
    role  = "machine-current-state"
  })
}

resource "azurerm_cosmosdb_sql_database" "machine_state" {
  name                = "industriepulse"
  resource_group_name = azurerm_resource_group.main.name
  account_name        = azurerm_cosmosdb_account.machine_state.name
}

resource "azurerm_cosmosdb_sql_container" "machine_state" {
  name                = "machine-state"
  resource_group_name = azurerm_resource_group.main.name
  account_name        = azurerm_cosmosdb_account.machine_state.name
  database_name       = azurerm_cosmosdb_sql_database.machine_state.name

  partition_key_paths   = ["/machineId"]
  partition_key_version = 2
}

resource "azurerm_servicebus_namespace" "maintenance" {
  name                = local.servicebus_namespace_name
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  sku                           = "Standard"
  minimum_tls_version           = "1.2"
  public_network_access_enabled = true
  local_auth_enabled            = true

  tags = merge(local.common_tags, {
    phase = "P5"
    role  = "maintenance-messaging"
  })
}

resource "azurerm_servicebus_queue" "maintenance_commands" {
  name         = "maintenance-commands"
  namespace_id = azurerm_servicebus_namespace.maintenance.id

  max_delivery_count  = 10
  lock_duration       = "PT1M"
  default_message_ttl = "P1D"

  requires_duplicate_detection            = true
  duplicate_detection_history_time_window = "PT10M"

  dead_lettering_on_message_expiration = true
}

resource "azurerm_servicebus_queue_authorization_rule" "maintenance_sender" {
  name     = "maintenance-sender"
  queue_id = azurerm_servicebus_queue.maintenance_commands.id

  send   = true
  listen = false
  manage = false
}

resource "azurerm_servicebus_queue_authorization_rule" "maintenance_receiver" {
  name     = "maintenance-receiver"
  queue_id = azurerm_servicebus_queue.maintenance_commands.id

  send   = false
  listen = true
  manage = false
}

resource "azurerm_servicebus_queue_authorization_rule" "maintenance_operations" {
  name     = "maintenance-operations"
  queue_id = azurerm_servicebus_queue.maintenance_commands.id

  send   = true
  listen = true
  manage = false
}
