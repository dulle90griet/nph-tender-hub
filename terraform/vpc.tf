# VPCs

resource "aws_vpc" "main" {
    cidr_block           = "10.0.0.0/16"
    instance_tenancy     = "default"
    enable_dns_hostnames = true
    enable_dns_support   = true
    
    tags = {
        Name = "${var.PREFIX}-vpc"
    }
}


# Subnets

locals {
    # Create a map of the public subnets to be created
    public_subnets = {
        a   = { cidr_block = "10.0.0.0/20", az = "${var.AWS_REGION}a" }
        b   = { cidr_block = "10.0.16.0/20", az = "${var.AWS_REGION}b" }
        c   = { cidr_block = "10.0.32.0/20", az = "${var.AWS_REGION}c" }
    }

    # Create a list of private subnet keys for easier indexing
    public_subnet_keys = keys(local.public_subnets)
}

resource "aws_subnet" "public" {
    for_each = local.public_subnets

    vpc_id            = aws_vpc.main.id
    cidr_block        = each.value.cidr_block
    availability_zone = each.value.az

    tags = {
        Name = "${var.PREFIX}-subnet-public${index(local.public_subnet_keys, each.key)+1}-${each.value.az}"
    }
}

/*
resource "aws_subnet" "public_a" {
    vpc_id            = aws_vpc.main.id
    cidr_block        = "10.0.0.0/20"
    availability_zone = "${var.AWS_REGION}a"

    tags = {
        Name = "${var.PREFIX}-subnet-public1-${var.AWS_REGION}a"
    }
}

resource "aws_subnet" "public_b" {
    vpc_id            = aws_vpc.main.id
    cidr_block        = "10.0.16.0/20"
    availability_zone = "${var.AWS_REGION}b"

    tags = {
        Name = "${var.PREFIX}-subnet-public2-${var.AWS_REGION}b"
    }
}

resource "aws_subnet" "public_c" {
    vpc_id            = aws_vpc.main.id
    cidr_block        = "10.0.32.0/20"
    availability_zone = "${var.AWS_REGION}c"
    
    tags = {
        Name = "${var.PREFIX}-subnet-public3-${var.AWS_REGION}c"
    }
}
*/

locals {
    # Create a map of the private subnets to be created
    private_subnets = {
        a   = { cidr_block = "10.0.128.0/20", az = "${var.AWS_REGION}a" }
        b   = { cidr_block = "10.0.144.0/20", az = "${var.AWS_REGION}b" }
        c   = { cidr_block = "10.0.160.0/20", az = "${var.AWS_REGION}c" }
    }

    # Create a list of private subnet keys for easier indexing
    private_subnet_keys = keys(local.private_subnets)
}

resource "aws_subnet" "private" {
    for_each = local.private_subnets

    vpc_id            = aws_vpc.main.id
    cidr_block        = each.value.cidr_block
    availability_zone = each.value.az

    tags = {
        Name = "${var.PREFIX}-subnet-private${index(local.private_subnet_keys, each.key)+1}-${each.value.az}"
    }
}

/*
resource "aws_subnet" "private_a" {
    vpc_id            = aws_vpc.main.id
    cidr_block        = "10.0.128.0/20"
    availability_zone = "${var.AWS_REGION}a"
    
    tags = {
        Name = "${var.PREFIX}-subnet-private1-${var.AWS_REGION}a"
    }
}

resource "aws_subnet" "private_b" {
    vpc_id            = aws_vpc.main.id
    cidr_block        = "10.0.144.0/20"
    availability_zone = "${var.AWS_REGION}b"
    
    tags = {
        Name = "${var.PREFIX}-subnet-private2-${var.AWS_REGION}b"
    }
}

resource "aws_subnet" "private_c" {
    vpc_id            = aws_vpc.main.id
    cidr_block        = "10.0.160.0/20"
    availability_zone = "${var.AWS_REGION}c"
    
    tags = {
        Name = "${var.PREFIX}-subnet-private3-${var.AWS_REGION}c"
    }
}
*/

# Create internet gateway

resource "aws_internet_gateway" "igw" {
    vpc_id = aws_vpc.main.id

    tags = {
        Name = "${var.PREFIX}-igw"
    }
}


# Create route table
resource "aws_route_table" "public" {
    vpc_id = aws_vpc.main.id

    route {
        cidr_block = "0.0.0.0/0"
        gateway_id = aws_internet_gateway.igw.id
    }

    tags = {
        Name = "${var.PREFIX}-rtb-public"
    }
}


# Associate route table
resource "aws_route_table_association" "public_a" {
    subnet_id      = aws_subnet.public["a"].id
    route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "public_b" {
    subnet_id      = aws_subnet.public["b"].id
    route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "public_c" {
    subnet_id      = aws_subnet.public["c"].id
    route_table_id = aws_route_table.public.id
}


# Allocate elastic IPs
resource "aws_eip" "nat" {
    for_each = { for idx in range(var.NAT_GATEWAY_COUNT): idx => null }

    domain = "vpc"

    tags = {
        Name = "${var.PREFIX}-nat-eip-${each.key+1}"
    }
}

/*
resource "aws_eip" "a" {
    domain = "vpc"
}
*/


# Create NAT gateways
locals {
    # Map each NAT Gateway to a public subnet using modulo round robin
    nat_to_subnet_map = {
        for idx in range(var.NAT_GATEWAY_COUNT):
            idx => local.private_subnet_keys[idx % length(local.private_subnet_keys)]
            if length(local.private_subnet_keys) > 0
    }
}

resource "aws_nat_gateway" "ngw" {
    for_each = aws_eip.nat

    allocation_id = aws_eip.nat[each.key].id
    subnet_id     = aws_subnet.public[local.nat_to_subnet_map[each.key]].id

    depends_on    = [ aws_internet_gateway.igw ]

    tags = {
        Name = "${var.PREFIX}-nat-public${each.key+1}-${var.AWS_REGION}${local.nat_to_subnet_map[each.key]}"
    }
}

/*
resource "aws_nat_gateway" "a" {
    allocation_id = aws_eip.a.id
    subnet_id     = aws_subnet.public["a"].id

    depends_on    = [ aws_internet_gateway.igw ]

    tags = {
        Name = "${var.PREFIX}-nat-public1-${var.AWS_REGION}"
    }
}
*/


# Create and associate route tables

locals {
    # Map each private subnet to a NAT Gateway using modulo operation
    subnet_to_nat_map = {
        for idx, subnet_key in local.private_subnet_keys:
            subnet_key => idx % var.NAT_GATEWAY_COUNT
            if var.NAT_GATEWAY_COUNT > 0
    }
}

resource "aws_route_table" "private" {
    for_each = { for idx in range(var.NAT_GATEWAY_COUNT): idx => null }

    vpc_id = aws_vpc.main.id

    route {
        cidr_block     = "0.0.0.0/0"
        nat_gateway_id = aws_nat_gateway.ngw[each.key].id
    }

    tags = {
        Name = "${var.PREFIX}-rtb-private${each.key+1}-${var.AWS_REGION}"
    }
}

resource "aws_route_table_association" "private" {
    for_each = local.subnet_to_nat_map
    
    subnet_id = aws_subnet.private[each.key].id
    route_table_id = aws_route_table.private[each.value].id
}

/*
resource "aws_route_table" "private_a" {
    vpc_id = aws_vpc.main.id

    route {
        cidr_block     = "0.0.0.0/0"
        nat_gateway_id = aws_nat_gateway.a.id
    }

    tags = {
        Name = "${var.PREFIX}-rtb-private1-${var.AWS_REGION}a"
    }
}

# Associate route table
resource "aws_route_table_association" "private_a" {
    subnet_id      = aws_subnet.private["a"].id
    route_table_id = aws_route_table.private_a.id
}


# Create route table
resource "aws_route_table" "private_b" {
    vpc_id = aws_vpc.main.id

    route {
        cidr_block     = "0.0.0.0/0"
        nat_gateway_id = aws_nat_gateway.a.id
    }

    tags = {
        Name = "${var.PREFIX}-rtb-private2-${var.AWS_REGION}b"
    }
}

# Associate route table
resource "aws_route_table_association" "private_b" {
    subnet_id      = aws_subnet.private["b"].id
    route_table_id = aws_route_table.private_b.id
}


# Create route table
resource "aws_route_table" "private_c" {
    vpc_id = aws_vpc.main.id

    route {
        cidr_block     = "0.0.0.0/0"
        nat_gateway_id = aws_nat_gateway.a.id
    }

    tags = {
        Name = "${var.PREFIX}-rtb-private3-${var.AWS_REGION}c"
    }
}

# Associate route table
resource "aws_route_table_association" "private_c" {
    subnet_id      = aws_subnet.private["c"].id
    route_table_id = aws_route_table.private_c.id
}
*/

# Create S3 endpoint and associate it with private subnet route tables
resource "aws_vpc_endpoint" "s3" {
    vpc_id            = aws_vpc.main.id
    vpc_endpoint_type = "Gateway"
    service_name      = "com.amazonaws.${var.AWS_REGION}.s3"

    # route_table_ids = [ for rtb in aws_route_table.private: rtb.id]

    tags = {
        Name = "${var.PREFIX}-vpce-s3"
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
    name = "${var.PREFIX}BudibaseFargateService"
    description = "Security group for ${var.CLIENT} ${var.PROJECT} Fargate Budibase deployment"
    vpc_id = aws_vpc.main.id
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
    name = "${var.PREFIX}BudibaseLoadBalancer"
    description = "Security group for ${var.CLIENT} ${var.PROJECT} Budibase load balancer"
    vpc_id = aws_vpc.main.id
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
    name = "${var.PREFIX}BudibaseEFS"
    description = "Security group for EFS access from ECS tasks"
    vpc_id = aws_vpc.main.id
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
