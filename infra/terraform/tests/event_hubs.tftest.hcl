mock_provider "azurerm" {}

run "event_hubs_module" {
  command = plan

  module {
    source = "./modules/event-hubs"
  }

  variables {
    resource_group_name = "rg-industriepulse-test-weu"
    location            = "westeurope"
    namespace_name      = "ehns-industriepulse-test-example"
    eventhub_name       = "telemetry"
    capacity            = 1
    partition_count     = 8
    retention_days      = 1

    tags = {
      project     = "IndustriePulse"
      environment = "test"
    }
  }

  assert {
    condition     = azurerm_eventhub_namespace.this.sku == "Standard"
    error_message = "Event Hubs namespace must use the Standard SKU."
  }

  assert {
    condition     = azurerm_eventhub_namespace.this.capacity == 1
    error_message = "Development capacity must be one throughput unit."
  }

  assert {
    condition     = azurerm_eventhub.telemetry.partition_count == 8
    error_message = "Telemetry Event Hub must use eight partitions."
  }

  assert {
    condition     = azurerm_eventhub.telemetry.message_retention == 1
    error_message = "Telemetry Event Hub must use one-day retention."
  }

  assert {
    condition     = azurerm_eventhub_authorization_rule.producer.send
    error_message = "Producer authorization rule must allow Send."
  }

  assert {
    condition     = !azurerm_eventhub_authorization_rule.producer.listen
    error_message = "Producer authorization rule must not allow Listen."
  }

  assert {
    condition     = !azurerm_eventhub_authorization_rule.producer.manage
    error_message = "Producer authorization rule must not allow Manage."
  }
}
