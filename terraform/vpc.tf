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
    subnet_id      = aws_subnet.public_a.id
    route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "public_b" {
    subnet_id      = aws_subnet.public_b.id
    route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "public_c" {
    subnet_id      = aws_subnet.public_c.id
    route_table_id = aws_route_table.public.id
}


# Allocate elastic IP eipalloc-0c59b697e45a00edf
resource "aws_eip" "a" {
    domain = "vpc"
}


# Create NAT gateway
resource "aws_nat_gateway" "a" {
    allocation_id = aws_eip.a.id
    subnet_id     = aws_subnet.public_a.id

    depends_on    = [ aws_internet_gateway.igw ]

    tags = {
        Name = "${var.PREFIX}-nat-public1-${var.AWS_REGION}"
    }
}


# Create route table
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
    subnet_id      = aws_subnet.private_a.id
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
    subnet_id      = aws_subnet.private_b.id
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
    subnet_id      = aws_subnet.private_c.id
    route_table_id = aws_route_table.private_c.id
}


# Associate S3 endpoint with private subnet route tables
resource "aws_vpc_endpoint" "s3" {
    vpc_id            = aws_vpc.main.id
    vpc_endpoint_type = "Gateway"
    service_name      = "com.amazonaws.${var.AWS_REGION}.s3"

    route_table_ids = [
        aws_route_table.private_a.id,
        aws_route_table.private_b.id,
        aws_route_table.private_c.id
    ]

    tags = {
        Name = "${var.PREFIX}-vpce-s3"
    }
}
