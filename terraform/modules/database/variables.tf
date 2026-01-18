variable "environment" {
  description = "Environment name"
  type        = string
}

variable "region" {
  description = "AWS region"
  type        = string
}

variable "cluster_identifier" {
  description = "RDS cluster identifier"
  type        = string
}

variable "database_name" {
  description = "Database name"
  type        = string
  default     = "yukyu"
}

variable "master_username" {
  description = "Master username"
  type        = string
  default     = "yukyu_admin"
  sensitive   = true
}

variable "master_password" {
  description = "Master password"
  type        = string
  sensitive   = true
}

variable "engine_version" {
  description = "PostgreSQL engine version"
  type        = string
  default     = "15.3"
}

variable "instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.r6g.large"
}

variable "allocated_storage" {
  description = "Allocated storage in GB"
  type        = number
  default     = 100
}

variable "backup_retention_days" {
  description = "Backup retention days"
  type        = number
  default     = 30
}

variable "preferred_backup_window" {
  description = "Preferred backup window"
  type        = string
  default     = "03:00-04:00"
}

variable "preferred_maintenance_window" {
  description = "Preferred maintenance window"
  type        = string
  default     = "mon:04:00-mon:05:00"
}

variable "monitoring_interval" {
  description = "Monitoring interval in seconds"
  type        = number
  default     = 60
}

variable "vpc_subnet_ids" {
  description = "VPC subnet IDs"
  type        = list(string)
}

variable "security_group_ids" {
  description = "Security group IDs"
  type        = list(string)
}

variable "kms_key_id" {
  description = "KMS key ID for encryption"
  type        = string
}

variable "is_read_replica" {
  description = "Whether this is a read replica"
  type        = bool
  default     = false
}

variable "replication_source_arn" {
  description = "Source cluster ARN for read replica"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
