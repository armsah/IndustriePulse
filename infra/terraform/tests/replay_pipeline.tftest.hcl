mock_provider "azurerm" {}

run "capture_and_replay_pipeline" {
  command = plan

  assert {
    condition     = azurerm_storage_account.telemetry_cold.account_tier == "Standard"
    error_message = "P7 cold storage must use Standard tier."
  }

  assert {
    condition     = azurerm_storage_account.telemetry_cold.account_replication_type == "LRS"
    error_message = "P7 cold storage must use LRS replication."
  }

  assert {
    condition     = azurerm_storage_account.telemetry_cold.access_tier == "Cool"
    error_message = "P7 cold storage must use the Cool access tier."
  }

  assert {
    condition     = azurerm_storage_container.telemetry_capture.name == "telemetry-capture"
    error_message = "P7 capture container name must be telemetry-capture."
  }

  assert {
    condition     = azurerm_storage_container.telemetry_capture.container_access_type == "private"
    error_message = "P7 capture container must remain private."
  }

  assert {
    condition     = module.event_hubs.capture_enabled == true
    error_message = "Telemetry Event Hubs Capture must be enabled for P7."
  }

  assert {
    condition     = azurerm_eventhub.telemetry_replay.name == "telemetry-replay"
    error_message = "Historical replay must use the isolated telemetry-replay Event Hub."
  }

  assert {
    condition     = azurerm_eventhub_consumer_group.replay_processor.name == "replay-processor"
    error_message = "Replay processor consumer group must exist."
  }

  assert {
    condition     = azurerm_eventhub_authorization_rule.replay_sender.send == true
    error_message = "Replay sender must have Send rights."
  }

  assert {
    condition     = azurerm_eventhub_authorization_rule.replay_sender.listen == false
    error_message = "Replay sender must not have Listen rights."
  }

  assert {
    condition     = azurerm_eventhub_authorization_rule.replay_sender.manage == false
    error_message = "Replay sender must not have Manage rights."
  }

  assert {
    condition     = azurerm_eventhub_authorization_rule.replay_receiver.listen == true
    error_message = "Replay receiver must have Listen rights."
  }

  assert {
    condition     = azurerm_eventhub_authorization_rule.replay_receiver.send == false
    error_message = "Replay receiver must not have Send rights."
  }

  assert {
    condition     = azurerm_eventhub_authorization_rule.replay_receiver.manage == false
    error_message = "Replay receiver must not have Manage rights."
  }
}
