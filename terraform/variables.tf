################################################################################
# YuKyuDATA Terraform Variables
################################################################################

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be development, staging, or production."
  }
}

variable "app_name" {
  description = "Application name"
  type        = string
  default     = "yukyu"
}

variable "domain_name" {
  description = "Primary domain name"
  type        = string
  default     = "yukyu-app.example.com"
}

################################################################################
# REGION CONFIGURATION
################################################################################

variable "primary_region" {
  description = "Primary AWS region"
  type        = string
  default     = "us-east-1"
}

variable "secondary_region" {
  description = "Secondary AWS region"
  type        = string
  default     = "us-west-1"
}

variable "tertiary_region" {
  description = "Tertiary AWS region (Disaster Recovery)"
  type        = string
  default     = "eu-west-1"
}

################################################################################
# NETWORK CONFIGURATION
################################################################################

variable "primary_vpc_cidr" {
  description = "Primary VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "secondary_vpc_cidr" {
  description = "Secondary VPC CIDR block"
  type        = string
  default     = "10.1.0.0/16"
}

variable "tertiary_vpc_cidr" {
  description = "Tertiary VPC CIDR block"
  type        = string
  default     = "10.2.0.0/16"
}

variable "primary_az_count" {
  description = "Number of availability zones in primary region"
  type        = number
  default     = 3
  validation {
    condition     = var.primary_az_count >= 2 && var.primary_az_count <= 4
    error_message = "AZ count must be between 2 and 4."
  }
}

variable "secondary_az_count" {
  description = "Number of availability zones in secondary region"
  type        = number
  default     = 2
}

variable "tertiary_az_count" {
  description = "Number of availability zones in tertiary region"
  type        = number
  default     = 2
}

################################################################################
# DATABASE CONFIGURATION
################################################################################

variable "database_name" {
  description = "PostgreSQL database name"
  type        = string
  default     = "yukyu"
  sensitive   = false
}

variable "database_username" {
  description = "PostgreSQL master username"
  type        = string
  default     = "yukyu_admin"
  sensitive   = true
}

variable "database_password" {
  description = "PostgreSQL master password"
  type        = string
  sensitive   = true
  validation {
    condition     = length(var.database_password) >= 16
    error_message = "Password must be at least 16 characters."
  }
}

variable "postgresql_version" {
  description = "PostgreSQL engine version"
  type        = string
  default     = "15.3"
}

variable "primary_db_instance_class" {
  description = "Primary database instance type"
  type        = string
  default     = "db.r6g.xlarge"  # 4vCPU, 32GB RAM
}

variable "secondary_db_instance_class" {
  description = "Secondary database instance type"
  type        = string
  default     = "db.r6g.large"   # 2vCPU, 16GB RAM
}

variable "tertiary_db_instance_class" {
  description = "Tertiary database instance type"
  type        = string
  default     = "db.r6g.large"   # 2vCPU, 16GB RAM
}

variable "primary_storage_gb" {
  description = "Primary database storage in GB"
  type        = number
  default     = 100
  validation {
    condition     = var.primary_storage_gb >= 20 && var.primary_storage_gb <= 1000
    error_message = "Storage must be between 20 and 1000 GB."
  }
}

variable "backup_retention_days" {
  description = "Database backup retention in days"
  type        = number
  default     = 30
  validation {
    condition     = var.backup_retention_days >= 7 && var.backup_retention_days <= 35
    error_message = "Retention must be between 7 and 35 days."
  }
}

variable "backup_window" {
  description = "Preferred backup window (UTC)"
  type        = string
  default     = "03:00-04:00"
}

variable "maintenance_window" {
  description = "Preferred maintenance window"
  type        = string
  default     = "mon:04:00-mon:05:00"
}

################################################################################
# COMPUTE CONFIGURATION
################################################################################

variable "app_image" {
  description = "Docker image for application"
  type        = string
  default     = "yukyu:latest"
}

variable "app_port" {
  description = "Application port"
  type        = number
  default     = 8000
}

variable "primary_instance_type" {
  description = "Primary EC2 instance type"
  type        = string
  default     = "t3.xlarge"
}

variable "secondary_instance_type" {
  description = "Secondary EC2 instance type"
  type        = string
  default     = "t3.large"
}

variable "primary_desired_capacity" {
  description = "Desired number of instances in primary region"
  type        = number
  default     = 3
}

variable "primary_min_capacity" {
  description = "Minimum number of instances in primary region"
  type        = number
  default     = 2
}

variable "primary_max_capacity" {
  description = "Maximum number of instances in primary region"
  type        = number
  default     = 10
}

variable "secondary_desired_capacity" {
  description = "Desired number of instances in secondary region"
  type        = number
  default     = 1
}

variable "secondary_max_capacity" {
  description = "Maximum number of instances in secondary region"
  type        = number
  default     = 5
}

################################################################################
# MONITORING CONFIGURATION
################################################################################

variable "prometheus_instance_type" {
  description = "Prometheus server instance type"
  type        = string
  default     = "t3.large"
}

variable "grafana_instance_type" {
  description = "Grafana server instance type"
  type        = string
  default     = "t3.medium"
}

variable "slack_webhook_url" {
  description = "Slack webhook URL for alerts"
  type        = string
  sensitive   = true
  default     = ""
}

################################################################################
# TAGS
################################################################################

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default = {
    Project     = "YuKyuDATA"
    ManagedBy   = "Terraform"
    Phase       = "Phase3-DevOps"
  }
}
