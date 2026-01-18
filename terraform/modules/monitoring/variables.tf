variable "environment" {
  description = "Environment name"
  type        = string
}

variable "region" {
  description = "AWS region"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "subnet_ids" {
  description = "Subnet IDs"
  type        = list(string)
}

variable "prometheus_instance_type" {
  description = "Prometheus instance type"
  type        = string
  default     = "t3.large"
}

variable "grafana_instance_type" {
  description = "Grafana instance type"
  type        = string
  default     = "t3.medium"
}

variable "app_cluster_arn" {
  description = "ECS cluster ARN for monitoring"
  type        = string
}

variable "enable_alerting" {
  description = "Enable AlertManager integration"
  type        = bool
  default     = true
}

variable "slack_webhook_url" {
  description = "Slack webhook URL for alerts"
  type        = string
  sensitive   = true
  default     = ""
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
