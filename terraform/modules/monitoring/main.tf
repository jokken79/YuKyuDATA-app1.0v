################################################################################
# Monitoring Module - Prometheus + Grafana + AlertManager
################################################################################

locals {
  name_prefix = "${var.environment}-${var.region}"
}

################################################################################
# EC2 INSTANCE - PROMETHEUS
################################################################################

resource "aws_instance" "prometheus" {
  ami           = data.aws_ami.amazon_linux_2.id
  instance_type = var.prometheus_instance_type
  subnet_id     = var.subnet_ids[0]

  iam_instance_profile = aws_iam_instance_profile.prometheus.name

  security_groups = [aws_security_group.prometheus.id]

  user_data = base64encode(templatefile("${path.module}/prometheus-setup.sh", {
    slack_webhook = var.slack_webhook_url
  }))

  root_block_device {
    volume_size           = 100
    volume_type           = "gp3"
    delete_on_termination = true
    encrypted             = true
  }

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-prometheus"
  })
}

################################################################################
# EC2 INSTANCE - GRAFANA
################################################################################

resource "aws_instance" "grafana" {
  ami           = data.aws_ami.amazon_linux_2.id
  instance_type = var.grafana_instance_type
  subnet_id     = var.subnet_ids[0]

  iam_instance_profile = aws_iam_instance_profile.grafana.name

  security_groups = [aws_security_group.grafana.id]

  user_data = base64encode(file("${path.module}/grafana-setup.sh"))

  root_block_device {
    volume_size           = 50
    volume_type           = "gp3"
    delete_on_termination = true
    encrypted             = true
  }

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-grafana"
  })
}

################################################################################
# SECURITY GROUPS
################################################################################

resource "aws_security_group" "prometheus" {
  name        = "${local.name_prefix}-prometheus-sg"
  description = "Security group for Prometheus"
  vpc_id      = data.aws_vpc.selected.id

  # Prometheus web UI
  ingress {
    from_port   = 9090
    to_port     = 9090
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # Should be restricted to internal/bastion
  }

  # Node Exporter
  ingress {
    from_port   = 9100
    to_port     = 9100
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # SSH
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # Should be restricted
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-prometheus-sg"
  })
}

resource "aws_security_group" "grafana" {
  name        = "${local.name_prefix}-grafana-sg"
  description = "Security group for Grafana"
  vpc_id      = data.aws_vpc.selected.id

  # Grafana web UI
  ingress {
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # Should be restricted
  }

  # SSH
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # Should be restricted
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-grafana-sg"
  })
}

################################################################################
# IAM ROLES & POLICIES
################################################################################

resource "aws_iam_role" "prometheus" {
  name = "${local.name_prefix}-prometheus-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "prometheus" {
  name = "${local.name_prefix}-prometheus-policy"
  role = aws_iam_role.prometheus.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ec2:DescribeInstances",
          "ec2:DescribeTags"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:GetMetricStatistics",
          "cloudwatch:ListMetrics"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams",
          "logs:GetLogEvents"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "rds:DescribeDBClusters",
          "rds:DescribeDBInstances"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_instance_profile" "prometheus" {
  name = "${local.name_prefix}-prometheus-profile"
  role = aws_iam_role.prometheus.name
}

resource "aws_iam_role" "grafana" {
  name = "${local.name_prefix}-grafana-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_instance_profile" "grafana" {
  name = "${local.name_prefix}-grafana-profile"
  role = aws_iam_role.grafana.name
}

################################################################################
# CLOUDWATCH LOG GROUP - MONITORING
################################################################################

resource "aws_cloudwatch_log_group" "prometheus" {
  name              = "/prometheus/${local.name_prefix}"
  retention_in_days = 30

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-prometheus-logs"
  })
}

resource "aws_cloudwatch_log_group" "grafana" {
  name              = "/grafana/${local.name_prefix}"
  retention_in_days = 30

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-grafana-logs"
  })
}

################################################################################
# ELASTIC IPs
################################################################################

resource "aws_eip" "prometheus" {
  instance = aws_instance.prometheus.id
  domain   = "vpc"

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-prometheus-eip"
  })

  depends_on = [data.aws_internet_gateway.selected]
}

resource "aws_eip" "grafana" {
  instance = aws_instance.grafana.id
  domain   = "vpc"

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-grafana-eip"
  })

  depends_on = [data.aws_internet_gateway.selected]
}

################################################################################
# DATA SOURCES
################################################################################

data "aws_vpc" "selected" {
  filter {
    name   = "tag:Name"
    values = ["*"]
  }
}

data "aws_internet_gateway" "selected" {
  filter {
    name   = "attachment.vpc-id"
    values = [data.aws_vpc.selected.id]
  }
}

data "aws_ami" "amazon_linux_2" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }

  filter {
    name   = "root-device-type"
    values = ["ebs"]
  }
}

################################################################################
# OUTPUTS
################################################################################

output "prometheus_endpoint" {
  description = "Prometheus instance IP"
  value       = aws_eip.prometheus.public_ip
}

output "prometheus_private_ip" {
  description = "Prometheus instance private IP"
  value       = aws_instance.prometheus.private_ip
}

output "grafana_endpoint" {
  description = "Grafana instance IP"
  value       = aws_eip.grafana.public_ip
}

output "grafana_private_ip" {
  description = "Grafana instance private IP"
  value       = aws_instance.grafana.private_ip
}

output "prometheus_instance_id" {
  description = "Prometheus instance ID"
  value       = aws_instance.prometheus.id
}

output "grafana_instance_id" {
  description = "Grafana instance ID"
  value       = aws_instance.grafana.id
}
