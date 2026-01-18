################################################################################
# YuKyuDATA Terraform Outputs
################################################################################

################################################################################
# PRIMARY REGION OUTPUTS
################################################################################

output "primary_alb_dns_name" {
  description = "Primary region load balancer DNS name"
  value       = module.primary_compute.alb_dns_name
}

output "primary_alb_zone_id" {
  description = "Primary region load balancer zone ID"
  value       = module.primary_compute.alb_zone_id
}

output "primary_database_endpoint" {
  description = "Primary database cluster endpoint (write)"
  value       = module.primary_database.endpoint
  sensitive   = false
}

output "primary_database_reader_endpoint" {
  description = "Primary database cluster reader endpoint (read)"
  value       = module.primary_database.reader_endpoint
  sensitive   = false
}

output "primary_database_port" {
  description = "Primary database port"
  value       = module.primary_database.port
}

output "primary_ecs_cluster_name" {
  description = "Primary ECS cluster name"
  value       = module.primary_compute.cluster_name
}

output "primary_ecs_cluster_arn" {
  description = "Primary ECS cluster ARN"
  value       = module.primary_compute.cluster_arn
}

################################################################################
# SECONDARY REGION OUTPUTS
################################################################################

output "secondary_alb_dns_name" {
  description = "Secondary region load balancer DNS name"
  value       = module.secondary_compute.alb_dns_name
}

output "secondary_alb_zone_id" {
  description = "Secondary region load balancer zone ID"
  value       = module.secondary_compute.alb_zone_id
}

output "secondary_database_reader_endpoint" {
  description = "Secondary database read replica endpoint"
  value       = module.secondary_database.reader_endpoint
  sensitive   = false
}

output "secondary_ecs_cluster_name" {
  description = "Secondary ECS cluster name"
  value       = module.secondary_compute.cluster_name
}

################################################################################
# TERTIARY REGION OUTPUTS (DISASTER RECOVERY)
################################################################################

output "tertiary_database_reader_endpoint" {
  description = "Tertiary database read replica endpoint (DR)"
  value       = module.tertiary_database.reader_endpoint
  sensitive   = false
}

################################################################################
# DNS & CDN OUTPUTS
################################################################################

output "route53_zone_id" {
  description = "Route53 hosted zone ID"
  value       = aws_route53_zone.yukyu.zone_id
}

output "route53_zone_nameservers" {
  description = "Route53 zone nameservers"
  value       = aws_route53_zone.yukyu.name_servers
}

output "cloudfront_domain_name" {
  description = "CloudFront distribution domain name"
  value       = aws_cloudfront_distribution.yukyu.domain_name
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID"
  value       = aws_cloudfront_distribution.yukyu.id
}

################################################################################
# BACKUP & SECURITY OUTPUTS
################################################################################

output "backup_vault_arn" {
  description = "AWS Backup vault ARN"
  value       = aws_backup_vault.yukyu_primary.arn
}

output "backup_vault_name" {
  description = "AWS Backup vault name"
  value       = aws_backup_vault.yukyu_primary.name
}

output "secrets_manager_database_secret_arn" {
  description = "Secrets Manager database credentials ARN"
  value       = aws_secretsmanager_secret.database_credentials.arn
  sensitive   = false
}

output "secrets_manager_database_secret_id" {
  description = "Secrets Manager database credentials ID"
  value       = aws_secretsmanager_secret.database_credentials.id
  sensitive   = false
}

output "kms_primary_key_id" {
  description = "Primary KMS encryption key ID"
  value       = aws_kms_key.primary_encryption.key_id
}

output "kms_primary_key_arn" {
  description = "Primary KMS encryption key ARN"
  value       = aws_kms_key.primary_encryption.arn
}

################################################################################
# MONITORING OUTPUTS
################################################################################

output "prometheus_endpoint" {
  description = "Prometheus server endpoint"
  value       = module.primary_monitoring.prometheus_endpoint
}

output "grafana_endpoint" {
  description = "Grafana server endpoint"
  value       = module.primary_monitoring.grafana_endpoint
}

output "prometheus_dashboard_url" {
  description = "Prometheus Dashboard URL"
  value       = "http://${module.primary_monitoring.prometheus_endpoint}:9090"
}

output "grafana_dashboard_url" {
  description = "Grafana Dashboard URL"
  value       = "http://${module.primary_monitoring.grafana_endpoint}:3000"
}

################################################################################
# SUMMARY OUTPUT
################################################################################

output "deployment_summary" {
  description = "Deployment configuration summary"
  value = {
    primary_region   = var.primary_region
    secondary_region = var.secondary_region
    tertiary_region  = var.tertiary_region

    primary_endpoint   = module.primary_compute.alb_dns_name
    secondary_endpoint = module.secondary_compute.alb_dns_name
    cdn_endpoint       = aws_cloudfront_distribution.yukyu.domain_name

    database_engine     = "PostgreSQL ${var.postgresql_version}"
    database_replication = "Cross-region with automatic failover"

    backup_strategy  = "Daily snapshots with ${var.backup_retention_days}-day retention"
    rto_minutes      = 15
    rpo_minutes      = 5

    monitoring = {
      prometheus = module.primary_monitoring.prometheus_endpoint
      grafana    = module.primary_monitoring.grafana_endpoint
      alerts_sns = aws_sns_topic.alerts.arn
    }

    security = {
      database_encryption_key = aws_kms_key.primary_encryption.key_id
      secrets_vault           = aws_secretsmanager_secret.database_credentials.arn
    }
  }
}

output "connection_strings" {
  description = "Connection strings for applications"
  value = {
    primary_write = "postgresql://${var.database_username}:***@${module.primary_database.endpoint}:5432/${var.database_name}"
    primary_read  = "postgresql://${var.database_username}:***@${module.primary_database.reader_endpoint}:5432/${var.database_name}"
    secondary_read = "postgresql://${var.database_username}:***@${module.secondary_database.reader_endpoint}:5432/${var.database_name}"
    tertiary_read = "postgresql://${var.database_username}:***@${module.tertiary_database.reader_endpoint}:5432/${var.database_name}"
  }
  sensitive = false
}

################################################################################
# HEALTH CHECKS OUTPUTS
################################################################################

output "health_check_ids" {
  description = "Route53 health check IDs"
  value = {
    primary   = aws_route53_health_check.primary.id
    secondary = aws_route53_health_check.secondary.id
  }
}

output "sns_alert_topic_arn" {
  description = "SNS topic for CloudWatch alarms"
  value       = aws_sns_topic.alerts.arn
}

output "sns_alert_topic_name" {
  description = "SNS topic name for alarms"
  value       = aws_sns_topic.alerts.name
}
