################################################################################
# Database Module - PostgreSQL Aurora RDS Cluster
################################################################################

locals {
  name_prefix = "${var.environment}-${var.region}"
}

################################################################################
# RDS SUBNET GROUP
################################################################################

resource "aws_db_subnet_group" "main" {
  name       = "${local.name_prefix}-db-subnet-group"
  subnet_ids = var.vpc_subnet_ids

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-db-subnet-group"
  })
}

################################################################################
# RDS SECURITY GROUP
################################################################################

resource "aws_security_group" "rds" {
  name        = "${local.name_prefix}-rds-sg"
  description = "Security group for RDS"
  vpc_id      = data.aws_vpc.selected.id

  dynamic "ingress" {
    for_each = var.security_group_ids
    content {
      from_port       = 5432
      to_port         = 5432
      protocol        = "tcp"
      security_groups = [ingress.value]
    }
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-rds-sg"
  })
}

################################################################################
# RDS AURORA CLUSTER
################################################################################

resource "aws_rds_cluster" "main" {
  cluster_identifier              = var.cluster_identifier
  engine                          = "aurora-postgresql"
  engine_version                  = var.engine_version
  database_name                   = var.database_name
  master_username                 = var.master_username
  master_password                 = var.master_password
  port                            = 5432

  # Network
  db_subnet_group_name            = aws_db_subnet_group.main.name
  vpc_security_group_ids          = concat(var.security_group_ids, [aws_security_group.rds.id])

  # Backup and Recovery
  backup_retention_period         = var.backup_retention_days
  preferred_backup_window         = var.preferred_backup_window
  preferred_maintenance_window    = var.preferred_maintenance_window
  copy_tags_to_snapshot           = true
  deletion_protection             = var.environment == "production" ? true : false

  # High Availability
  enable_http_endpoint            = true
  enable_https_endpoint           = false

  # Encryption
  storage_encrypted               = true
  kms_key_id                      = var.kms_key_id

  # Monitoring
  enable_cloudwatch_logs_exports  = ["postgresql"]
  db_cluster_parameter_group_name = aws_rds_cluster_parameter_group.main.name

  # Failover
  enable_global_write_forwarding  = false
  skip_final_snapshot             = var.environment != "production"

  # Cross-region replication (if applicable)
  dynamic "replication_source_arn" {
    for_each = var.is_read_replica ? [var.replication_source_arn] : []
    content {
      replication_source_arn = replication_source_arn.value
    }
  }

  tags = merge(var.tags, {
    Name = var.cluster_identifier
  })
}

################################################################################
# RDS CLUSTER INSTANCES
################################################################################

resource "aws_rds_cluster_instance" "main" {
  count = var.is_read_replica ? 1 : 2  # 1 instance for read replica, 2 for primary (HA)

  cluster_identifier           = aws_rds_cluster.main.id
  identifier                   = "${var.cluster_identifier}-${count.index + 1}"
  instance_class               = var.instance_class
  engine                       = aws_rds_cluster.main.engine
  engine_version               = aws_rds_cluster.main.engine_version
  publicly_accessible          = false
  auto_minor_version_upgrade   = true

  # Performance Insights
  performance_insights_enabled = var.environment == "production" ? true : false

  # Enhanced Monitoring
  monitoring_interval          = var.monitoring_interval
  monitoring_role_arn          = aws_iam_role.rds_monitoring.arn

  tags = merge(var.tags, {
    Name = "${var.cluster_identifier}-${count.index + 1}"
  })
}

################################################################################
# RDS CLUSTER PARAMETER GROUP
################################################################################

resource "aws_rds_cluster_parameter_group" "main" {
  name        = "${local.name_prefix}-pg-cluster-params"
  family      = "aurora-postgresql${var.engine_version}"
  description = "Cluster parameter group for ${var.cluster_identifier}"

  parameter {
    name  = "rds.force_ssl"
    value = "0"  # Can be enabled if using SSL
  }

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-pg-cluster-params"
  })
}

################################################################################
# RDS INSTANCE PARAMETER GROUP
################################################################################

resource "aws_db_parameter_group" "main" {
  name        = "${local.name_prefix}-pg-instance-params"
  family      = "aurora-postgresql${var.engine_version}"
  description = "Instance parameter group for ${var.cluster_identifier}"

  parameter {
    name  = "log_statement"
    value = "all"
  }

  parameter {
    name  = "log_min_duration_statement"
    value = "1000"  # Log queries taking > 1 second
  }

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-pg-instance-params"
  })
}

################################################################################
# IAM ROLE FOR ENHANCED MONITORING
################################################################################

resource "aws_iam_role" "rds_monitoring" {
  name = "${local.name_prefix}-rds-monitoring-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "monitoring.rds.amazonaws.com"
        }
      }
    ]
  })

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-rds-monitoring-role"
  })
}

resource "aws_iam_role_policy_attachment" "rds_monitoring" {
  role       = aws_iam_role.rds_monitoring.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

################################################################################
# CLOUDWATCH LOG GROUP
################################################################################

resource "aws_cloudwatch_log_group" "postgresql" {
  name              = "/aws/rds/cluster/${var.cluster_identifier}/postgresql"
  retention_in_days = var.backup_retention_days

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-pg-logs"
  })
}

################################################################################
# DATA SOURCES
################################################################################

data "aws_vpc" "selected" {
  filter {
    name   = "tag:Name"
    values = ["*"]  # Will be filtered by module caller
  }
}

################################################################################
# OUTPUTS
################################################################################

output "cluster_id" {
  description = "RDS cluster ID"
  value       = aws_rds_cluster.main.id
}

output "cluster_arn" {
  description = "RDS cluster ARN"
  value       = aws_rds_cluster.main.arn
}

output "endpoint" {
  description = "RDS cluster write endpoint"
  value       = aws_rds_cluster.main.endpoint
}

output "reader_endpoint" {
  description = "RDS cluster read endpoint"
  value       = aws_rds_cluster.main.reader_endpoint
}

output "port" {
  description = "RDS cluster port"
  value       = aws_rds_cluster.main.port
}

output "database_name" {
  description = "Database name"
  value       = aws_rds_cluster.main.database_name
}

output "security_group_id" {
  description = "RDS security group ID"
  value       = aws_security_group.rds.id
}

output "monitoring_role_arn" {
  description = "RDS monitoring role ARN"
  value       = aws_iam_role.rds_monitoring.arn
}
