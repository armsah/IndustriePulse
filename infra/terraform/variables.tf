variable "location" {
  description = "Azure region for IndustriePulse P2 resources."
  type        = string
  default     = "westeurope"
}

variable "environment" {
  description = "Deployment environment name."
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "test", "prod"], var.environment)
    error_message = "environment must be one of: dev, test, prod."
  }
}

variable "eventhub_capacity" {
  description = "Event Hubs Standard throughput units. ADR-003 uses 1 TU for normal development."
  type        = number
  default     = 1

  validation {
    condition     = var.eventhub_capacity >= 1
    error_message = "eventhub_capacity must be at least 1."
  }
}

variable "telemetry_partition_count" {
  description = "Partition count for the live telemetry Event Hub, defined by ADR-003."
  type        = number
  default     = 8

  validation {
    condition     = var.telemetry_partition_count == 8
    error_message = "ADR-003 fixes the P2 telemetry Event Hub at 8 partitions."
  }
}

variable "telemetry_retention_days" {
  description = "Telemetry retention inside Event Hubs, defined by ADR-003."
  type        = number
  default     = 1

  validation {
    condition     = var.telemetry_retention_days == 1
    error_message = "ADR-003 fixes P2 Event Hubs retention at 1 day."
  }
}
