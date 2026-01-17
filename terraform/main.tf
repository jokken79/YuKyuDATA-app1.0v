################################################################################
# YuKyuDATA Multi-Region Deployment - Main Terraform Configuration
# FASE 3: DevOps Maturity - Infrastructure as Code
################################################################################

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "yukyu-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "yukyu-terraform-locks"
  }
}

################################################################################
# PROVIDERS - Multi-Region Configuration
################################################################################

# Primary Region (us-east-1)
provider "aws" {
  alias  = "primary"
  region = var.primary_region

  default_tags {
    tags = {
      Project     = "YuKyuDATA"
      Environment = var.environment
      ManagedBy   = "Terraform"
      Phase       = "Phase3-DevOps"
      CreatedAt   = timestamp()
    }
  }
}

# Secondary Region (us-west-1)
provider "aws" {
  alias  = "secondary"
  region = var.secondary_region

  default_tags {
    tags = {
      Project     = "YuKyuDATA"
      Environment = var.environment
      ManagedBy   = "Terraform"
      Phase       = "Phase3-DevOps"
    }
  }
}

# Tertiary Region (eu-west-1)
provider "aws" {
  alias  = "tertiary"
  region = var.tertiary_region

  default_tags {
    tags = {
      Project     = "YuKyuDATA"
      Environment = var.environment
      ManagedBy   = "Terraform"
      Phase       = "Phase3-DevOps"
    }
  }
}

################################################################################
# DATA SOURCES
################################################################################

# Current AWS Account
data "aws_caller_identity" "current" {
  provider = aws.primary
}

# Availability Zones
data "aws_availability_zones" "primary" {
  provider = aws.primary
  state    = "available"
}

data "aws_availability_zones" "secondary" {
  provider = aws.secondary
  state    = "available"
}

data "aws_availability_zones" "tertiary" {
  provider = aws.tertiary
  state    = "available"
}

################################################################################
# PRIMARY REGION - Complete Stack
################################################################################

# Network (VPC, Subnets, Security Groups)
module "primary_network" {
  source   = "./modules/networking"
  providers = {
    aws = aws.primary
  }

  environment = var.environment
  vpc_cidr    = var.primary_vpc_cidr
  region      = var.primary_region
  az_count    = var.primary_az_count

  enable_nat_gateway = true
  enable_vpn_gateway = true
}

# Database - PostgreSQL Primary Cluster
module "primary_database" {
  source   = "./modules/database"
  providers = {
    aws = aws.primary
  }

  environment           = var.environment
  cluster_identifier    = "${var.app_name}-primary"
  database_name         = var.database_name
  master_username       = var.database_username
  master_password       = var.database_password
  engine_version        = var.postgresql_version
  instance_class        = var.primary_db_instance_class
  allocated_storage     = var.primary_storage_gb
  backup_retention_days = var.backup_retention_days

  vpc_subnet_ids = module.primary_network.private_subnet_ids
  security_group_ids = [
    module.primary_database.security_group_id,
    module.primary_network.database_security_group_id
  ]

  enable_backtrack              = true
  enable_backup_window          = true
  preferred_backup_window       = var.backup_window
  preferred_maintenance_window  = var.maintenance_window

  enable_enhanced_monitoring    = true
  monitoring_interval           = 60

  enable_cluster_encryption     = true
  kms_key_id                    = aws_kms_key.primary_encryption.arn

  tags = {
    Role = "Primary"
    RTO  = "15min"
    RPO  = "5min"
  }
}

# Compute - Application Servers (ECS on EC2)
module "primary_compute" {
  source   = "./modules/compute"
  providers = {
    aws = aws.primary
  }

  environment = var.environment
  cluster_name = "${var.app_name}-primary"
  region = var.primary_region

  app_image = var.app_image
  app_port = var.app_port

  vpc_id = module.primary_network.vpc_id
  subnet_ids = module.primary_network.private_subnet_ids

  alb_security_group_id = module.primary_network.alb_security_group_id
  app_security_group_id = module.primary_network.app_security_group_id

  desired_capacity = var.primary_desired_capacity
  min_capacity = var.primary_min_capacity
  max_capacity = var.primary_max_capacity

  instance_type = var.primary_instance_type

  database_url = module.primary_database.endpoint
  database_secret_arn = aws_secretsmanager_secret.database_credentials.arn

  tags = {
    Role = "Primary"
  }
}

# Monitoring - Prometheus + Grafana
module "primary_monitoring" {
  source   = "./modules/monitoring"
  providers = {
    aws = aws.primary
  }

  environment = var.environment
  region = var.primary_region

  vpc_id = module.primary_network.vpc_id
  subnet_ids = module.primary_network.private_subnet_ids

  prometheus_instance_type = var.prometheus_instance_type
  grafana_instance_type = var.grafana_instance_type

  app_cluster_arn = module.primary_compute.cluster_arn

  enable_alerting = true
  slack_webhook_url = var.slack_webhook_url

  tags = {
    Role = "Monitoring"
  }
}

################################################################################
# SECONDARY REGION - Read Replicas Only
################################################################################

# Network
module "secondary_network" {
  source   = "./modules/networking"
  providers = {
    aws = aws.secondary
  }

  environment = var.environment
  vpc_cidr    = var.secondary_vpc_cidr
  region      = var.secondary_region
  az_count    = var.secondary_az_count

  enable_nat_gateway = true
  enable_vpn_gateway = false
}

# Database - PostgreSQL Read Replica
module "secondary_database" {
  source   = "./modules/database"
  providers = {
    aws = aws.secondary
  }

  environment = var.environment

  # Create as cross-region read replica
  replication_source_arn = module.primary_database.cluster_arn
  cluster_identifier = "${var.app_name}-secondary"

  instance_class = var.secondary_db_instance_class

  vpc_subnet_ids = module.secondary_network.private_subnet_ids
  security_group_ids = [
    module.secondary_database.security_group_id,
    module.secondary_network.database_security_group_id
  ]

  is_read_replica = true

  enable_enhanced_monitoring = true
  monitoring_interval = 60

  tags = {
    Role = "Secondary-ReadReplica"
    RTO = "1min"
  }
}

# Compute - Standby Application Servers
module "secondary_compute" {
  source   = "./modules/compute"
  providers = {
    aws = aws.secondary
  }

  environment = var.environment
  cluster_name = "${var.app_name}-secondary"
  region = var.secondary_region

  app_image = var.app_image
  app_port = var.app_port

  vpc_id = module.secondary_network.vpc_id
  subnet_ids = module.secondary_network.private_subnet_ids

  alb_security_group_id = module.secondary_network.alb_security_group_id
  app_security_group_id = module.secondary_network.app_security_group_id

  desired_capacity = var.secondary_desired_capacity
  min_capacity = 1  # Minimal in secondary
  max_capacity = var.secondary_max_capacity

  instance_type = var.secondary_instance_type

  # Read replica endpoint - read-only mode
  database_url = module.secondary_database.reader_endpoint
  database_secret_arn = aws_secretsmanager_secret.database_credentials.arn
  database_read_only = true

  tags = {
    Role = "Secondary-Standby"
  }
}

################################################################################
# TERTIARY REGION - Disaster Recovery + CDN
################################################################################

# Network
module "tertiary_network" {
  source   = "./modules/networking"
  providers = {
    aws = aws.tertiary
  }

  environment = var.environment
  vpc_cidr    = var.tertiary_vpc_cidr
  region      = var.tertiary_region
  az_count    = var.tertiary_az_count

  enable_nat_gateway = true
  enable_vpn_gateway = false
}

# Database - Read Replica for DR
module "tertiary_database" {
  source   = "./modules/database"
  providers = {
    aws = aws.tertiary
  }

  environment = var.environment
  replication_source_arn = module.primary_database.cluster_arn
  cluster_identifier = "${var.app_name}-tertiary"

  instance_class = var.tertiary_db_instance_class
  vpc_subnet_ids = module.tertiary_network.private_subnet_ids
  security_group_ids = [
    module.tertiary_database.security_group_id,
    module.tertiary_network.database_security_group_id
  ]

  is_read_replica = true
  enable_enhanced_monitoring = true
  monitoring_interval = 60

  tags = {
    Role = "Tertiary-DR"
    RTO = "5min"
  }
}

################################################################################
# CROSS-REGION COMPONENTS
################################################################################

# Route53 Health Checks + Failover
resource "aws_route53_zone" "yukyu" {
  provider = aws.primary
  name     = var.domain_name
}

# Health check - Primary region
resource "aws_route53_health_check" "primary" {
  provider = aws.primary

  ip_address = module.primary_compute.alb_endpoint
  port       = var.app_port
  type       = "HTTP"
  resource_path = "/api/health"
  failure_threshold = 3
  request_interval = 30
  measure_latency = true
  alarm_enabled = true

  tags = {
    Name = "yukyu-primary-health"
  }
}

# Health check - Secondary region
resource "aws_route53_health_check" "secondary" {
  provider = aws.primary

  ip_address = module.secondary_compute.alb_endpoint
  port       = var.app_port
  type       = "HTTP"
  resource_path = "/api/health"
  failure_threshold = 3
  request_interval = 30
  measure_latency = true

  tags = {
    Name = "yukyu-secondary-health"
  }
}

# Route53 Records - Failover configuration
resource "aws_route53_record" "app_primary" {
  provider = aws.primary

  zone_id = aws_route53_zone.yukyu.zone_id
  name    = var.domain_name
  type    = "A"
  alias {
    name                   = module.primary_compute.alb_dns_name
    zone_id                = module.primary_compute.alb_zone_id
    evaluate_target_health = true
  }

  set_identifier = "primary"
  failover_routing_policy {
    type = "PRIMARY"
  }

  health_check_id = aws_route53_health_check.primary.id
}

resource "aws_route53_record" "app_secondary" {
  provider = aws.primary

  zone_id = aws_route53_zone.yukyu.zone_id
  name    = var.domain_name
  type    = "A"
  alias {
    name                   = module.secondary_compute.alb_dns_name
    zone_id                = module.secondary_compute.alb_zone_id
    evaluate_target_health = true
  }

  set_identifier = "secondary"
  failover_routing_policy {
    type = "SECONDARY"
  }
}

# CloudFront Distribution - CDN + Failover
resource "aws_cloudfront_distribution" "yukyu" {
  provider = aws.primary

  enabled = true
  is_ipv6_enabled = true

  # Origin - Primary + Secondary for failover
  origin {
    domain_name = module.primary_compute.alb_dns_name
    origin_id   = "primary"

    custom_origin_config {
      http_port = var.app_port
      https_port = 443
      origin_protocol_policy = "http-only"
      origin_ssl_protocols = ["TLSv1.2"]
    }
  }

  origin {
    domain_name = module.secondary_compute.alb_dns_name
    origin_id   = "secondary"

    custom_origin_config {
      http_port = var.app_port
      https_port = 443
      origin_protocol_policy = "http-only"
      origin_ssl_protocols = ["TLSv1.2"]
    }
  }

  default_cache_behavior {
    allowed_methods = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods  = ["GET", "HEAD"]
    target_origin_id = "primary"

    forwarded_values {
      query_string = true
      headers = ["*"]

      cookies {
        forward = "all"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl = 0
    default_ttl = 0
    max_ttl = 0
    compress = true
  }

  # Origin group with failover
  origin_group {
    origin_id = "failover"

    failover_criteria {
      status_codes = [500, 502, 503, 504]
    }

    member {
      origin_id = "primary"
    }

    member {
      origin_id = "secondary"
    }
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  tags = {
    Name = "yukyu-cdn"
  }
}

################################################################################
# SECRETS & ENCRYPTION
################################################################################

# KMS Key - Primary region encryption
resource "aws_kms_key" "primary_encryption" {
  provider = aws.primary

  description = "KMS key for YuKyuDATA primary region"
  deletion_window_in_days = 10
  enable_key_rotation = true

  tags = {
    Name = "yukyu-primary-key"
  }
}

resource "aws_kms_alias" "primary_encryption" {
  provider = aws.primary

  name = "alias/yukyu-primary"
  target_key_id = aws_kms_key.primary_encryption.key_id
}

# Database Credentials - Secrets Manager
resource "aws_secretsmanager_secret" "database_credentials" {
  provider = aws.primary

  name = "yukyu/database/credentials"
  recovery_window_in_days = 7
  kms_key_id = aws_kms_key.primary_encryption.id

  tags = {
    Name = "yukyu-db-credentials"
  }
}

resource "aws_secretsmanager_secret_version" "database_credentials" {
  provider = aws.primary

  secret_id = aws_secretsmanager_secret.database_credentials.id
  secret_string = jsonencode({
    username = var.database_username
    password = var.database_password
    engine = "postgres"
    host = module.primary_database.endpoint
    port = 5432
    dbname = var.database_name
  })
}

# JWT Secret
resource "aws_secretsmanager_secret" "jwt_secret" {
  provider = aws.primary

  name = "yukyu/jwt/secret"
  recovery_window_in_days = 7

  tags = {
    Name = "yukyu-jwt-secret"
  }
}

################################################################################
# BACKUP VAULT - Cross-region backups
################################################################################

resource "aws_backup_vault" "yukyu_primary" {
  provider = aws.primary

  name = "${var.app_name}-backups-primary"
  kms_key_arn = aws_kms_key.primary_encryption.arn

  tags = {
    Name = "yukyu-backup-vault-primary"
  }
}

# Backup plan - Daily snapshots with 30-day retention
resource "aws_backup_plan" "yukyu" {
  provider = aws.primary

  name = "${var.app_name}-backup-plan"

  rule {
    rule_name         = "daily_snapshots"
    target_backup_vault_name = aws_backup_vault.yukyu_primary.name
    schedule          = "cron(0 5 * * ? *)" # 5 AM UTC daily
    start_window      = 60
    completion_window = 120

    lifecycle {
      delete_after = var.backup_retention_days
      cold_storage_after = 30  # Move to cold storage after 30 days
    }

    copy_action {
      destination_vault_arn = aws_backup_vault.yukyu_primary.arn

      lifecycle {
        delete_after = var.backup_retention_days
      }
    }
  }

  tags = {
    Name = "yukyu-backup-plan"
  }
}

################################################################################
# CLOUDWATCH ALARMS - Critical Monitoring
################################################################################

# RDS Primary - Replication Lag
resource "aws_cloudwatch_metric_alarm" "replication_lag" {
  provider = aws.primary

  alarm_name = "yukyu-replication-lag-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods = 2
  metric_name = "AuroraBinlogReplicaLag"
  namespace = "AWS/RDS"
  period = 300
  statistic = "Average"
  threshold = 1000  # milliseconds
  alarm_description = "Alert when replication lag exceeds 1 second"
  alarm_actions = [aws_sns_topic.alerts.arn]

  dimensions = {
    DBClusterIdentifier = module.primary_database.cluster_id
  }
}

# Database CPU Utilization
resource "aws_cloudwatch_metric_alarm" "database_cpu" {
  provider = aws.primary

  alarm_name = "yukyu-database-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods = 2
  metric_name = "CPUUtilization"
  namespace = "AWS/RDS"
  period = 300
  statistic = "Average"
  threshold = 80
  alarm_description = "Alert when database CPU exceeds 80%"
  alarm_actions = [aws_sns_topic.alerts.arn]

  dimensions = {
    DBClusterIdentifier = module.primary_database.cluster_id
  }
}

# SNS Topic for Alerts
resource "aws_sns_topic" "alerts" {
  provider = aws.primary

  name = "${var.app_name}-alerts"
  kms_master_key_id = aws_kms_key.primary_encryption.id

  tags = {
    Name = "yukyu-alerts"
  }
}

################################################################################
# OUTPUTS
################################################################################

output "primary_region" {
  description = "Primary region configuration"
  value = {
    region = var.primary_region
    vpc_id = module.primary_network.vpc_id
    alb_endpoint = module.primary_compute.alb_endpoint
    database_endpoint = module.primary_database.endpoint
    database_reader_endpoint = module.primary_database.reader_endpoint
  }
}

output "secondary_region" {
  description = "Secondary region configuration"
  value = {
    region = var.secondary_region
    vpc_id = module.secondary_network.vpc_id
    alb_endpoint = module.secondary_compute.alb_endpoint
    database_endpoint = module.secondary_database.reader_endpoint
  }
}

output "tertiary_region" {
  description = "Tertiary region configuration"
  value = {
    region = var.tertiary_region
    vpc_id = module.tertiary_network.vpc_id
    database_endpoint = module.tertiary_database.reader_endpoint
  }
}

output "cloudfront_domain_name" {
  description = "CloudFront distribution domain"
  value = aws_cloudfront_distribution.yukyu.domain_name
}

output "route53_zone_id" {
  description = "Route53 zone ID"
  value = aws_route53_zone.yukyu.zone_id
}

output "backup_vault_arn" {
  description = "Backup vault ARN"
  value = aws_backup_vault.yukyu_primary.arn
}

output "secrets_manager_database_arn" {
  description = "Secrets Manager database credentials ARN"
  value = aws_secretsmanager_secret.database_credentials.arn
}
