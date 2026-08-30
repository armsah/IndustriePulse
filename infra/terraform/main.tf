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
  cold_storage_name         = "stipcold${var.environment}${local.subscription_suffix}"
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

resource "azurerm_storage_account" "telemetry_cold" {
  name                     = local.cold_storage_name
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"

  access_tier                     = "Cool"
  https_traffic_only_enabled      = true
  min_tls_version                 = "TLS1_2"
  allow_nested_items_to_be_public = false
  public_network_access_enabled   = true

  tags = merge(local.common_tags, {
    phase = "P7"
    role  = "telemetry-cold-storage"
  })
}

resource "azurerm_storage_container" "telemetry_capture" {
  name                  = "telemetry-capture"
  storage_account_id    = azurerm_storage_account.telemetry_cold.id
  container_access_type = "private"
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

  capture_enabled            = true
  capture_storage_account_id = azurerm_storage_account.telemetry_cold.id
  capture_container_name     = azurerm_storage_container.telemetry_capture.name

  tags = local.common_tags

  depends_on = [
    azurerm_storage_container.telemetry_capture
  ]
}

resource "azurerm_eventhub" "telemetry_replay" {
  name              = "telemetry-replay"
  namespace_id      = module.event_hubs.namespace_id
  partition_count   = var.telemetry_partition_count
  message_retention = 1
}

resource "azurerm_eventhub_consumer_group" "replay_processor" {
  name                = "replay-processor"
  namespace_name      = module.event_hubs.namespace_name
  eventhub_name       = azurerm_eventhub.telemetry_replay.name
  resource_group_name = azurerm_resource_group.main.name
}

resource "azurerm_eventhub_authorization_rule" "replay_sender" {
  name                = "telemetry-replay-sender"
  namespace_name      = module.event_hubs.namespace_name
  eventhub_name       = azurerm_eventhub.telemetry_replay.name
  resource_group_name = azurerm_resource_group.main.name

  listen = false
  send   = true
  manage = false
}

resource "azurerm_eventhub_authorization_rule" "replay_receiver" {
  name                = "telemetry-replay-receiver"
  namespace_name      = module.event_hubs.namespace_name
  eventhub_name       = azurerm_eventhub.telemetry_replay.name
  resource_group_name = azurerm_resource_group.main.name

  listen = true
  send   = false
  manage = false
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

locals {
  container_registry_name = "acr${local.project}${var.environment}${local.subscription_suffix}"
  container_app_env_name  = "cae-${local.project}-${var.environment}"
  api_container_app_name  = "ca-${local.project}-api-${var.environment}"
}

resource "azurerm_container_registry" "api" {
  name                = local.container_registry_name
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location

  sku           = "Basic"
  admin_enabled = true

  public_network_access_enabled = true

  tags = merge(local.common_tags, {
    phase = "P8"
    role  = "api-container-registry"
  })
}

resource "azurerm_container_app_environment" "api" {
  name                = local.container_app_env_name
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  tags = merge(local.common_tags, {
    phase = "P8"
    role  = "api-ui-runtime"
  })
}

resource "azurerm_container_app" "api" {
  name                         = local.api_container_app_name
  container_app_environment_id = azurerm_container_app_environment.api.id
  resource_group_name          = azurerm_resource_group.main.name
  revision_mode                = "Single"

  secret {
    name  = "registry-password"
    value = azurerm_container_registry.api.admin_password
  }

  secret {
    name  = "cosmos-connection-string"
    value = azurerm_cosmosdb_account.machine_state.primary_sql_connection_string
  }

  registry {
    server               = azurerm_container_registry.api.login_server
    username             = azurerm_container_registry.api.admin_username
    password_secret_name = "registry-password"
  }

  ingress {
    external_enabled = true
    target_port      = 8080

    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  template {
    min_replicas = 0
    max_replicas = 3

    container {
      name   = "industriepulse-api"
      image  = "${azurerm_container_registry.api.login_server}/industriepulse-api:${var.api_image_tag}"
      cpu    = 0.25
      memory = "0.5Gi"

      env {
        name        = "Cosmos__ConnectionString"
        secret_name = "cosmos-connection-string"
      }

      env {
        name  = "Cosmos__DatabaseName"
        value = azurerm_cosmosdb_sql_database.machine_state.name
      }

      env {
        name  = "Cosmos__ContainerName"
        value = azurerm_cosmosdb_sql_container.machine_state.name
      }

      liveness_probe {
        transport = "HTTP"
        port      = 8080
        path      = "/health"

        initial_delay           = 10
        interval_seconds        = 30
        timeout                 = 5
        failure_count_threshold = 3
      }

      readiness_probe {
        transport = "HTTP"
        port      = 8080
        path      = "/health"

        interval_seconds        = 10
        timeout                 = 5
        failure_count_threshold = 3
        success_count_threshold = 1
      }
    }
  }

  tags = merge(local.common_tags, {
    phase = "P8"
    role  = "api-ui"
  })
}
