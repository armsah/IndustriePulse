mock_provider "azurerm" {}

run "maintenance_messaging_contract" {
  command = plan

  assert {
    condition     = azurerm_servicebus_namespace.maintenance.sku == "Standard"
    error_message = "P5 Service Bus namespace must use Standard SKU."
  }

  assert {
    condition     = azurerm_servicebus_queue.maintenance_commands.name == "maintenance-commands"
    error_message = "P5 maintenance command queue must be named maintenance-commands."
  }

  assert {
    condition     = azurerm_servicebus_queue.maintenance_commands.requires_duplicate_detection == true
    error_message = "Maintenance command queue must enable duplicate detection."
  }

  assert {
    condition     = azurerm_servicebus_queue.maintenance_commands.max_delivery_count == 10
    error_message = "Maintenance command queue must retain the expected max delivery count."
  }

  assert {
    condition     = azurerm_servicebus_queue_authorization_rule.maintenance_sender.send == true
    error_message = "Maintenance sender authorization rule must allow Send."
  }

  assert {
    condition     = azurerm_servicebus_queue_authorization_rule.maintenance_sender.listen == false
    error_message = "Maintenance sender authorization rule must not allow Listen."
  }

  assert {
    condition     = azurerm_servicebus_queue_authorization_rule.maintenance_sender.manage == false
    error_message = "Maintenance sender authorization rule must not allow Manage."
  }

  assert {
    condition     = azurerm_servicebus_queue_authorization_rule.maintenance_receiver.listen == true
    error_message = "Maintenance receiver must have Listen permission."
  }

  assert {
    condition     = azurerm_servicebus_queue_authorization_rule.maintenance_receiver.send == false
    error_message = "Maintenance receiver must not have Send permission."
  }

  assert {
    condition     = azurerm_servicebus_queue_authorization_rule.maintenance_receiver.manage == false
    error_message = "Maintenance receiver must not have Manage permission."
  }

  assert {
    condition     = azurerm_servicebus_queue_authorization_rule.maintenance_operations.send == true
    error_message = "P6 maintenance operations rule must allow Send."
  }

  assert {
    condition     = azurerm_servicebus_queue_authorization_rule.maintenance_operations.listen == true
    error_message = "P6 maintenance operations rule must allow Listen."
  }

  assert {
    condition     = azurerm_servicebus_queue_authorization_rule.maintenance_operations.manage == false
    error_message = "P6 maintenance operations rule must not allow Manage."
  }
}
