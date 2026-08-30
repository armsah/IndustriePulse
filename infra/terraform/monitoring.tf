resource "azurerm_log_analytics_workspace" "observability" {
  name                = "${azurerm_resource_group.main.name}-observability"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  sku               = "PerGB2018"
  retention_in_days = 30
  daily_quota_gb    = 0.5

  tags = {
    project = "IndustriePulse"
    phase   = "P9"
  }
}

resource "azurerm_application_insights" "consumer" {
  name                = "${azurerm_resource_group.main.name}-consumer-ai"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  workspace_id     = azurerm_log_analytics_workspace.observability.id
  application_type = "other"

  retention_in_days = 30

  tags = {
    project = "IndustriePulse"
    phase   = "P9"
  }
}

resource "azurerm_application_insights_workbook" "consumer_observability" {
  name                = "9e50a142-9b31-4af4-93de-f7c50c42d9a1"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  display_name        = "IndustriePulse - Consumer Observability"

  data_json = jsonencode({
    version = "Notebook/1.0"

    items = [
      {
        type = 1
        content = {
          json = <<-MARKDOWN
          # IndustriePulse Consumer Observability

          Azure Monitor dashboard for Event Hubs consumer processing health.

          **P9 primary signal:** `consumer.processing.lag.events`

          Lag is calculated as:

          `partition head sequence number - sequence number currently being processed`

          Values are clamped to zero.

          Lag is a processing-position metric. It is not a durable checkpoint-lag metric.
          MARKDOWN
        }
        name = "overview"
      },
      {
        type = 3
        content = {
          version      = "KqlItem/1.0"
          query        = <<-KQL
          customMetrics
          | where name == "consumer.processing.lag.events"
          | summarize
              MaxLagEvents = max(valueMax),
              MinLagEvents = min(valueMin)
              by bin(timestamp, 1m)
          | order by timestamp asc
          | render timechart
          KQL
          size         = 0
          title        = "Processing lag"
          queryType    = 0
          resourceType = "microsoft.insights/components"
          crossComponentResources = [
            azurerm_application_insights.consumer.id
          ]
        }
        name = "processing-lag"
      },
      {
        type = 3
        content = {
          version      = "KqlItem/1.0"
          query        = <<-KQL
          customMetrics
          | where name == "consumer.event.age.ms"
          | summarize
              EventAgeSum = sum(valueSum),
              EventAgeCount = sum(valueCount),
              MaxEventAgeMs = max(valueMax)
              by bin(timestamp, 1m)
          | extend AverageEventAgeMs = iff(
              EventAgeCount > 0,
              EventAgeSum / EventAgeCount,
              real(null)
            )
          | project timestamp, AverageEventAgeMs, MaxEventAgeMs
          | order by timestamp asc
          | render timechart
          KQL
          size         = 0
          title        = "Event age"
          queryType    = 0
          resourceType = "microsoft.insights/components"
          crossComponentResources = [
            azurerm_application_insights.consumer.id
          ]
        }
        name = "event-age"
      },
      {
        type = 3
        content = {
          version      = "KqlItem/1.0"
          query        = <<-KQL
          customMetrics
          | where name in (
              "consumer.events.processed",
              "consumer.events.failed",
              "consumer.checkpoints"
          )
          | summarize Total = sum(valueSum) by name, bin(timestamp, 1m)
          | order by timestamp asc
          | render timechart
          KQL
          size         = 0
          title        = "Processing outcomes"
          queryType    = 0
          resourceType = "microsoft.insights/components"
          crossComponentResources = [
            azurerm_application_insights.consumer.id
          ]
        }
        name = "processing-outcomes"
      },
      {
        type = 3
        content = {
          version      = "KqlItem/1.0"
          query        = <<-KQL
          customMetrics
          | where name == "consumer.processing.duration.ms"
          | summarize
              DurationSum = sum(valueSum),
              DurationCount = sum(valueCount),
              MaxDurationMs = max(valueMax)
              by bin(timestamp, 1m)
          | extend AverageDurationMs = iff(
              DurationCount > 0,
              DurationSum / DurationCount,
              real(null)
            )
          | project timestamp, AverageDurationMs, MaxDurationMs
          | order by timestamp asc
          | render timechart
          KQL
          size         = 0
          title        = "Processing duration"
          queryType    = 0
          resourceType = "microsoft.insights/components"
          crossComponentResources = [
            azurerm_application_insights.consumer.id
          ]
        }
        name = "processing-duration"
      }
    ]

    isLocked = false

    fallbackResourceIds = [
      azurerm_application_insights.consumer.id
    ]
  })

  tags = {
    project = "IndustriePulse"
    phase   = "P9"
  }
}
