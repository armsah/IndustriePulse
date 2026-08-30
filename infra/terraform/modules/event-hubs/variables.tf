variable "resource_group_name" {
  description = "Name of the resource group containing Event Hubs."
  type        = string
}

variable "location" {
  description = "Azure region for the Event Hubs resources."
  type        = string
}

variable "namespace_name" {
  description = "Globally unique Event Hubs namespace name."
  type        = string
}

variable "eventhub_name" {
  description = "Name of the telemetry Event Hub."
  type        = string
  default     = "telemetry"
}

variable "capacity" {
  description = "Event Hubs Standard throughput-unit capacity."
  type        = number
  default     = 1

  validation {
    condition     = var.capacity >= 1
    error_message = "capacity must be at least 1."
  }
}

variable "partition_count" {
  description = "Number of partitions for the telemetry Event Hub."
  type        = number
  default     = 8

  validation {
    condition     = var.partition_count >= 1 && var.partition_count <= 32
    error_message = "partition_count must be between 1 and 32."
  }
}

variable "retention_days" {
  description = "Event Hub message retention in days."
  type        = number
  default     = 1

  validation {
    condition     = var.retention_days >= 1 && var.retention_days <= 7
    error_message = "retention_days must be between 1 and 7 for this Standard-tier module."
  }
}

variable "tags" {
  description = "Tags applied to supported Azure resources."
  type        = map(string)
  default     = {}
}

variable "capture_enabled" {
  description = "Enable Event Hubs Capture for telemetry."
  type        = bool
  default     = false
}

variable "capture_storage_account_id" {
  description = "Storage account resource ID used by Event Hubs Capture."
  type        = string
  default     = null
}

variable "capture_container_name" {
  description = "Blob container used by Event Hubs Capture."
  type        = string
  default     = null
}
