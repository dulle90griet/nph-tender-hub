# VPCs

resource "aws_vpc" "main" {
    count = var.ENVIRONMENT == "shared" ? 1 : 0

    cidr_block           = "10.0.0.0/16"
    instance_tenancy     = "default"
    enable_dns_hostnames = true
    enable_dns_support   = true
    
    tags = {
        Name        = "${var.PREFIX}-shared-vpc"
        Environment = "shared"
    }

    lifecycle {
        prevent_destroy = false
    }
}

data "aws_vpc" "main" {
    count = var.ENVIRONMENT == "shared" ? 0 : 1

    tags = {
        Name = "${var.PREFIX}-shared-vpc"
    }
}

locals {
    vpc_id = var.ENVIRONMENT == "shared" ? aws_vpc.main[0].id : data.aws_vpc.main[0].id
}


# Subnets

locals {
    # Create a map of the public subnets to be created
    public_subnets = {
        # Three public subnets for Budibase ALB dev
        a   = { cidr_block = "10.0.0.0/21", az = "${var.AWS_REGION}a" }
        b   = { cidr_block = "10.0.8.0/21", az = "${var.AWS_REGION}b" }
        c   = { cidr_block = "10.0.16.0/21", az = "${var.AWS_REGION}c" }

        # Three public subnets for Budibase ALB stage
        d   = { cidr_block = "10.0.24.0/21", az = "${var.AWS_REGION}a" }
        e   = { cidr_block = "10.0.32.0/21", az = "${var.AWS_REGION}b" }
        f   = { cidr_block = "10.0.40.0/21", az = "${var.AWS_REGION}c" }

        # Three public subnets for Budibase ALB prod
        g   = { cidr_block = "10.0.48.0/21", az = "${var.AWS_REGION}a" }
        h   = { cidr_block = "10.0.56.0/21", az = "${var.AWS_REGION}b" }
        i   = { cidr_block = "10.0.64.0/21", az = "${var.AWS_REGION}c" }
    }

    # Create a list of private subnet keys for easier indexing
    public_subnets_in_env = var.SUBNETS_BY_ENV[var.ENVIRONMENT]
}

resource "aws_subnet" "public" {
    for_each = {
        for key in local.public_subnets_in_env:
            key => local.public_subnets[key]
    }

    vpc_id            = local.vpc_id
    cidr_block        = each.value.cidr_block
    availability_zone = each.value.az

    tags = {
        Name = "${var.PREFIX}-${var.ENVIRONMENT}-subnet-public${index(local.public_subnets_in_env, each.key)+1}-${each.value.az}"
    }
}

locals {
    # Create a map of the private subnets to be created
    private_subnets = {
        # Three private subnets for Budibase/ECS dev
        a   = { cidr_block = "10.0.128.0/21", az = "${var.AWS_REGION}a" }
        b   = { cidr_block = "10.0.136.0/21", az = "${var.AWS_REGION}b" }
        c   = { cidr_block = "10.0.144.0/21", az = "${var.AWS_REGION}c" }
        
        # Three private subnets for Budibase/ECS stage
        d   = { cidr_block = "10.0.152.0/21", az = "${var.AWS_REGION}a" }
        e   = { cidr_block = "10.0.160.0/21", az = "${var.AWS_REGION}b" }
        f   = { cidr_block = "10.0.168.0/21", az = "${var.AWS_REGION}c" }

        # Three private subnets for Budibase/ECS prod
        g   = { cidr_block = "10.0.176.0/21", az = "${var.AWS_REGION}a" }
        h   = { cidr_block = "10.0.184.0/21", az = "${var.AWS_REGION}b" }
        i   = { cidr_block = "10.0.192.0/21", az = "${var.AWS_REGION}c" }

        # Three private subnets for RDS
        j   = { cidr_block = "10.0.200.0/21", az = "${var.AWS_REGION}a" }
        k   = { cidr_block = "10.0.208.0/21", az = "${var.AWS_REGION}b" }
        l   = { cidr_block = "10.0.216.0/21", az = "${var.AWS_REGION}c" }
    }

    # Create a list of the private subnet keys for use in the current environment
    private_subnets_in_env = var.SUBNETS_BY_ENV[var.ENVIRONMENT]
}

resource "aws_subnet" "private" {
    for_each = {
        for key in local.private_subnets_in_env:
            key => local.private_subnets[key]
    }

    vpc_id            = local.vpc_id
    cidr_block        = each.value.cidr_block
    availability_zone = each.value.az

    tags = {
        Name = "${var.PREFIX}-${var.ENVIRONMENT}-subnet-private${index(local.private_subnets_in_env, each.key)+1}-${each.value.az}"
    }
}


# Create internet gateway

resource "aws_internet_gateway" "igw" {
    vpc_id = local.vpc_id

    tags = {
        Name = "${var.PREFIX}-${var.ENVIRONMENT}-igw"
    }
}


# Create route table

resource "aws_route_table" "public" {
    vpc_id = local.vpc_id

    route {
        cidr_block = "0.0.0.0/0"
        gateway_id = aws_internet_gateway.igw.id
    }

    tags = {
        Name = "${var.PREFIX}-${var.ENVIRONMENT}-rtb-public"
    }
}


# Associate route table

resource "aws_route_table_association" "public" {
    for_each = aws_subnet.public

    subnet_id      = each.value.id
    route_table_id = aws_route_table.public.id
}


# Allocate elastic IPs

resource "aws_eip" "nat" {
    for_each = { for idx in range(var.NAT_GATEWAY_COUNT): idx => null }

    domain = "vpc"

    tags = {
        Name = "${var.PREFIX}-${var.ENVIRONMENT}-nat-eip-${each.key+1}"
    }
}


# Create NAT gateways

locals {
    # Map each NAT Gateway to a public subnet using modulo round robin
    nat_to_subnet_map = {
        for idx in range(var.NAT_GATEWAY_COUNT):
            idx => local.private_subnets_in_env[idx % length(local.private_subnets_in_env)]
            if length(local.private_subnets_in_env) > 0
    }
}

resource "aws_nat_gateway" "ngw" {
    for_each = aws_eip.nat

    allocation_id = aws_eip.nat[each.key].id
    subnet_id     = aws_subnet.public[local.nat_to_subnet_map[each.key]].id

    depends_on    = [ aws_internet_gateway.igw ]

    tags = {
        Name = "${var.PREFIX}-${var.ENVIRONMENT}-nat-public${each.key+1}-${var.AWS_REGION}${local.nat_to_subnet_map[each.key]}"
    }
}


# Create and associate route tables

locals {
    # Map each private subnet to a NAT Gateway using modulo operation
    subnet_to_nat_map = {
        for idx, subnet_key in local.private_subnets_in_env:
            subnet_key => idx % var.NAT_GATEWAY_COUNT
            if var.NAT_GATEWAY_COUNT > 0
    }
}

resource "aws_route_table" "private" {
    for_each = { for idx in range(var.NAT_GATEWAY_COUNT): idx => null }

    vpc_id = local.vpc_id

    route {
        cidr_block     = "0.0.0.0/0"
        nat_gateway_id = aws_nat_gateway.ngw[each.key].id
    }

    tags = {
        Name = "${var.PREFIX}-${var.ENVIRONMENT}-rtb-private${each.key+1}-${var.AWS_REGION}"
    }
}

resource "aws_route_table_association" "private" {
    for_each = local.subnet_to_nat_map
    
    subnet_id = aws_subnet.private[each.key].id
    route_table_id = aws_route_table.private[each.value].id
}


# Create S3 endpoint and associate it with private subnet route tables

resource "aws_vpc_endpoint" "s3" {
    vpc_id            = local.vpc_id
    vpc_endpoint_type = "Gateway"
    service_name      = "com.amazonaws.${var.AWS_REGION}.s3"

    # route_table_ids = [ for rtb in aws_route_table.private: rtb.id]

    tags = {
        Name = "${var.PREFIX}-${var.ENVIRONMENT}-vpce-s3"
    }

    lifecycle {
        create_before_destroy = true
    }
}

resource "aws_vpc_endpoint_route_table_association" "s3" {
    for_each = aws_route_table.private

    route_table_id = aws_route_table.private[each.key].id
    vpc_endpoint_id = aws_vpc_endpoint.s3.id
}


# Create security groups

resource "aws_security_group" "budibase_fargate" {
    name = "${var.PREFIX}${var.ENVIRONMENT}BudibaseFargateService"
    description = "Security group for ${var.CLIENT} ${var.PROJECT} Fargate Budibase deployment in ${var.ENVIRONMENT} environment"
    vpc_id = local.vpc_id
}

resource "aws_vpc_security_group_egress_rule" "allow_fargate_egress" {
    security_group_id = aws_security_group.budibase_fargate.id
    ip_protocol = -1
    cidr_ipv4 = "0.0.0.0/0"
}

resource "aws_vpc_security_group_ingress_rule" "allow_inbound_from_lb" {
    security_group_id = aws_security_group.budibase_fargate.id
    ip_protocol = "tcp"
    from_port = 80
    to_port = 80
    referenced_security_group_id = aws_security_group.budibase_load_balancer.id
}

resource "aws_security_group" "budibase_load_balancer" {
    name = "${var.PREFIX}${var.ENVIRONMENT}BudibaseLoadBalancer"
    description = "Security group for ${var.CLIENT} ${var.PROJECT} Budibase load balancer"
    vpc_id = local.vpc_id
}

resource "aws_vpc_security_group_egress_rule" "allow_lb_egress" {
    security_group_id = aws_security_group.budibase_load_balancer.id
    ip_protocol = -1
    cidr_ipv4 = "0.0.0.0/0"
}

resource "aws_vpc_security_group_ingress_rule" "allow_inbound_to_lb" {
    security_group_id = aws_security_group.budibase_load_balancer.id
    cidr_ipv4   = "0.0.0.0/0"
    ip_protocol = "tcp"
    from_port   = 80
    to_port     = 80
}

resource "aws_security_group" "budibase_efs" {
    name = "${var.PREFIX}${var.ENVIRONMENT}BudibaseEFS"
    description = "Security group for EFS access from ECS tasks"
    vpc_id = local.vpc_id
}

resource "aws_vpc_security_group_egress_rule" "allow_efs_egress" {
    security_group_id = aws_security_group.budibase_efs.id
    ip_protocol = -1
    cidr_ipv4 = "0.0.0.0/0"
}

resource "aws_vpc_security_group_ingress_rule" "allow_nfs_ingress_to_efs" {
    security_group_id = aws_security_group.budibase_efs.id
    from_port = 2049
    to_port = 2049
    ip_protocol = "tcp"
    referenced_security_group_id = aws_security_group.budibase_fargate.id
} 
