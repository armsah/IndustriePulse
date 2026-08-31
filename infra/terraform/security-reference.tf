locals {
  security_reference_count = var.security_reference_enabled ? 1 : 0

  private_dns_zones = {
    servicebus = "privatelink.servicebus.windows.net"
    blob       = "privatelink.blob.core.windows.net"
    cosmos     = "privatelink.documents.azure.com"
  }
}

resource "azurerm_virtual_network" "security_reference" {
  count = local.security_reference_count

  name                = format("vnet-%s-%s-private-reference", local.project, var.environment)
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  address_space       = ["10.40.0.0/16"]

  tags = merge(local.common_tags, {
    phase = "P11"
    role  = "private-reference-network"
  })
}

resource "azurerm_subnet" "private_endpoints" {
  count = local.security_reference_count

  name                 = "snet-private-endpoints"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.security_reference[0].name
  address_prefixes     = ["10.40.1.0/24"]

  private_endpoint_network_policies = "Disabled"
}

resource "azurerm_subnet" "container_apps" {
  count = local.security_reference_count

  name                 = "snet-container-apps"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.security_reference[0].name
  address_prefixes     = ["10.40.8.0/21"]

  delegation {
    name = "container-apps"

    service_delegation {
      name = "Microsoft.App/environments"
    }
  }
}

resource "azurerm_private_dns_zone" "security_reference" {
  for_each = var.security_reference_enabled ? local.private_dns_zones : {}

  name                = each.value
  resource_group_name = azurerm_resource_group.main.name

  tags = merge(local.common_tags, {
    phase = "P11"
    role  = "private-dns"
  })
}

resource "azurerm_private_dns_zone_virtual_network_link" "security_reference" {
  for_each = var.security_reference_enabled ? local.private_dns_zones : {}

  name                = "link-${each.key}"
  private_dns_zone_id = azurerm_private_dns_zone.security_reference[each.key].id
  virtual_network_id  = azurerm_virtual_network.security_reference[0].id

  registration_enabled = false
}

resource "azurerm_user_assigned_identity" "api_runtime" {
  count = local.security_reference_count

  name                = format("id-%s-api-%s", local.project, var.environment)
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  tags = merge(local.common_tags, {
    phase = "P11"
    role  = "api-runtime-identity"
  })
}

resource "azurerm_user_assigned_identity" "consumer_runtime" {
  count = local.security_reference_count

  name                = format("id-%s-consumer-%s", local.project, var.environment)
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  tags = merge(local.common_tags, {
    phase = "P11"
    role  = "telemetry-consumer-identity"
  })
}

resource "azurerm_role_assignment" "api_acr_pull" {
  count = local.security_reference_count

  scope                = azurerm_container_registry.api.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_user_assigned_identity.api_runtime[0].principal_id
}

resource "azurerm_role_assignment" "consumer_eventhub_receiver" {
  count = local.security_reference_count

  scope                = module.event_hubs.eventhub_id
  role_definition_name = "Azure Event Hubs Data Receiver"
  principal_id         = azurerm_user_assigned_identity.consumer_runtime[0].principal_id
}

resource "azurerm_role_assignment" "consumer_servicebus_sender" {
  count = local.security_reference_count

  scope                = azurerm_servicebus_queue.maintenance_commands.id
  role_definition_name = "Azure Service Bus Data Sender"
  principal_id         = azurerm_user_assigned_identity.consumer_runtime[0].principal_id
}

resource "azurerm_role_assignment" "consumer_checkpoint_blob" {
  count = local.security_reference_count

  scope                = azurerm_storage_account.checkpoints.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_user_assigned_identity.consumer_runtime[0].principal_id
}

resource "azurerm_cosmosdb_sql_role_assignment" "api_machine_state_reader" {
  count = local.security_reference_count

  resource_group_name = azurerm_resource_group.main.name
  account_name        = azurerm_cosmosdb_account.machine_state.name
  role_definition_id  = format("%s/sqlRoleDefinitions/00000000-0000-0000-0000-000000000001", azurerm_cosmosdb_account.machine_state.id)
  principal_id        = azurerm_user_assigned_identity.api_runtime[0].principal_id
  scope               = azurerm_cosmosdb_account.machine_state.id
}

resource "azurerm_cosmosdb_sql_role_assignment" "consumer_machine_state_contributor" {
  count = local.security_reference_count

  resource_group_name = azurerm_resource_group.main.name
  account_name        = azurerm_cosmosdb_account.machine_state.name
  role_definition_id  = format("%s/sqlRoleDefinitions/00000000-0000-0000-0000-000000000002", azurerm_cosmosdb_account.machine_state.id)
  principal_id        = azurerm_user_assigned_identity.consumer_runtime[0].principal_id
  scope               = azurerm_cosmosdb_account.machine_state.id
}

resource "azurerm_private_endpoint" "event_hubs" {
  count = local.security_reference_count

  name                = format("pe-%s-eventhubs-%s", local.project, var.environment)
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  subnet_id           = azurerm_subnet.private_endpoints[0].id

  private_service_connection {
    name                           = "psc-eventhubs"
    private_connection_resource_id = module.event_hubs.namespace_id
    subresource_names              = ["namespace"]
    is_manual_connection           = false
  }

  private_dns_zone_group {
    name                 = "default"
    private_dns_zone_ids = [azurerm_private_dns_zone.security_reference["servicebus"].id]
  }
}

resource "azurerm_private_endpoint" "service_bus" {
  count = local.security_reference_count

  name                = format("pe-%s-servicebus-%s", local.project, var.environment)
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  subnet_id           = azurerm_subnet.private_endpoints[0].id

  private_service_connection {
    name                           = "psc-servicebus"
    private_connection_resource_id = azurerm_servicebus_namespace.maintenance.id
    subresource_names              = ["namespace"]
    is_manual_connection           = false
  }

  private_dns_zone_group {
    name                 = "default"
    private_dns_zone_ids = [azurerm_private_dns_zone.security_reference["servicebus"].id]
  }
}

resource "azurerm_private_endpoint" "cosmos" {
  count = local.security_reference_count

  name                = format("pe-%s-cosmos-%s", local.project, var.environment)
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  subnet_id           = azurerm_subnet.private_endpoints[0].id

  private_service_connection {
    name                           = "psc-cosmos"
    private_connection_resource_id = azurerm_cosmosdb_account.machine_state.id
    subresource_names              = ["Sql"]
    is_manual_connection           = false
  }

  private_dns_zone_group {
    name                 = "default"
    private_dns_zone_ids = [azurerm_private_dns_zone.security_reference["cosmos"].id]
  }
}

resource "azurerm_private_endpoint" "checkpoints" {
  count = local.security_reference_count

  name                = format("pe-%s-checkpoints-%s", local.project, var.environment)
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  subnet_id           = azurerm_subnet.private_endpoints[0].id

  private_service_connection {
    name                           = "psc-checkpoints"
    private_connection_resource_id = azurerm_storage_account.checkpoints.id
    subresource_names              = ["blob"]
    is_manual_connection           = false
  }

  private_dns_zone_group {
    name                 = "default"
    private_dns_zone_ids = [azurerm_private_dns_zone.security_reference["blob"].id]
  }
}

resource "azurerm_private_endpoint" "telemetry_cold" {
  count = local.security_reference_count

  name                = format("pe-%s-capture-%s", local.project, var.environment)
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  subnet_id           = azurerm_subnet.private_endpoints[0].id

  private_service_connection {
    name                           = "psc-capture"
    private_connection_resource_id = azurerm_storage_account.telemetry_cold.id
    subresource_names              = ["blob"]
    is_manual_connection           = false
  }

  private_dns_zone_group {
    name                 = "default"
    private_dns_zone_ids = [azurerm_private_dns_zone.security_reference["blob"].id]
  }
}
