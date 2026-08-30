mock_provider "azurerm" {}

run "container_apps_api_ui" {
  command = plan

  assert {
    condition     = azurerm_container_registry.api.sku == "Basic"
    error_message = "P8 development registry must use the cost-optimized Basic SKU."
  }

  assert {
    condition     = azurerm_container_app.api.revision_mode == "Single"
    error_message = "P8 API/UI must use single-revision mode."
  }

  assert {
    condition     = azurerm_container_app.api.ingress[0].external_enabled == true
    error_message = "P8 API/UI must expose external HTTPS ingress."
  }

  assert {
    condition     = azurerm_container_app.api.ingress[0].target_port == 8080
    error_message = "P8 API/UI ingress must target port 8080."
  }

  assert {
    condition     = azurerm_container_app.api.template[0].min_replicas == 0
    error_message = "P8 development deployment must scale to zero."
  }

  assert {
    condition     = azurerm_container_app.api.template[0].max_replicas == 3
    error_message = "P8 development deployment must cap scale-out at three replicas."
  }

  assert {
    condition     = azurerm_container_app.api.template[0].container[0].cpu == 0.25
    error_message = "P8 API/UI must use the small development CPU allocation."
  }

  assert {
    condition     = azurerm_container_app.api.template[0].container[0].memory == "0.5Gi"
    error_message = "P8 API/UI must use the small development memory allocation."
  }
}
