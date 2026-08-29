terraform {
  required_version = ">= 1.15.0, < 2.0.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "5.2.0"
    }
  }
}

provider "azurerm" {
  features {}
}

module "event_hubs" {
  source = "../../modules/event-hubs"

  resource_group_name = "rg-example"
  location            = "westeurope"
  namespace_name      = "replace-with-globally-unique-name"

  eventhub_name   = "telemetry"
  capacity        = 1
  partition_count = 8
  retention_days  = 1

  tags = {
    project     = "IndustriePulse"
    environment = "example"
  }
}
