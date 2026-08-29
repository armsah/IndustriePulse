mock_provider "azurerm" {}

run "machine_state_store" {
  command = plan

  assert {
    condition = contains(
      [for capability in azurerm_cosmosdb_account.machine_state.capabilities : capability.name],
      "EnableServerless"
    )
    error_message = "Cosmos DB account must use serverless capability."
  }

  assert {
    condition     = azurerm_cosmosdb_account.machine_state.consistency_policy[0].consistency_level == "Session"
    error_message = "Cosmos DB account must use Session consistency."
  }

  assert {
    condition     = azurerm_cosmosdb_sql_database.machine_state.name == "industriepulse"
    error_message = "Machine-state database must be named industriepulse."
  }

  assert {
    condition     = azurerm_cosmosdb_sql_container.machine_state.name == "machine-state"
    error_message = "Machine-state container must be named machine-state."
  }

  assert {
    condition = contains(
      azurerm_cosmosdb_sql_container.machine_state.partition_key_paths,
      "/machineId"
    )
    error_message = "Machine-state container must partition by /machineId."
  }

  assert {
    condition     = length(azurerm_cosmosdb_sql_container.machine_state.partition_key_paths) == 1
    error_message = "Machine-state container must define exactly one partition-key path."
  }

  assert {
    condition     = azurerm_cosmosdb_sql_container.machine_state.partition_key_version == 2
    error_message = "Machine-state container must use partition key version 2."
  }
}
