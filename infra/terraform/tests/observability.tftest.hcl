mock_provider "azurerm" {}

override_resource {
  target          = azurerm_log_analytics_workspace.observability
  override_during = plan

  values = {
    id = "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/mock-rg/providers/Microsoft.OperationalInsights/workspaces/mock-observability"
  }
}

override_resource {
  target          = azurerm_application_insights.consumer
  override_during = plan

  values = {
    id = "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/mock-rg/providers/Microsoft.Insights/components/mock-consumer-ai"
  }
}

run "observability_resources" {
  command = plan

  assert {
    condition     = azurerm_log_analytics_workspace.observability.sku == "PerGB2018"
    error_message = "P9 Log Analytics must use the PerGB2018 SKU."
  }

  assert {
    condition     = azurerm_log_analytics_workspace.observability.retention_in_days == 30
    error_message = "P9 Log Analytics retention must be 30 days."
  }

  assert {
    condition     = azurerm_log_analytics_workspace.observability.daily_quota_gb == 0.5
    error_message = "P9 Log Analytics must retain the dev ingestion quota."
  }

  assert {
    condition = (
      azurerm_application_insights.consumer.workspace_id ==
      azurerm_log_analytics_workspace.observability.id
    )
    error_message = "Application Insights must be workspace-based."
  }

  assert {
    condition = strcontains(
      azurerm_application_insights_workbook.consumer_observability.data_json,
      "consumer.processing.lag.events"
    )
    error_message = "Workbook must contain the processing lag metric."
  }

  assert {
    condition = strcontains(
      azurerm_application_insights_workbook.consumer_observability.data_json,
      "consumer.event.age.ms"
    )
    error_message = "Workbook must contain the event age metric."
  }

  assert {
    condition = strcontains(
      azurerm_application_insights_workbook.consumer_observability.data_json,
      "consumer.events.failed"
    )
    error_message = "Workbook must expose processing failures."
  }
}