# Constants for use throughout the TF deployment

# Variables set using .tfvars files

variable "ENVIRONMENT" {
    type        = string
    description = "The environment to use (shared, dev, stage or prod)"

    validation {
        condition     = contains(["shared", "dev", "stage", "prod"], var.ENVIRONMENT)
        error_message = "Environment must be 'shared', 'dev', 'stage' or 'prod'."
    }
}

variable "AWS_REGION" {
    type        = string
    description = "The region in which to deploy our AWS resources"
}

variable "PREFIX" {
    type        = string
    description = "The string to prepend to all resource names associated with this project"
}

variable "CLIENT" {
    type        = string
    description = "The name of the client who has commissioned the current project"
}

variable "PROJECT" {
    type        = string
    description = "The name of the current project"
}

variable "REPO_NAME" {
    type        = string
    description = "The name of the current repository"
}

variable "IAM_USER" {
    type        = string
    description = "The name of the dev IAM user"
    default     = "nph_developer"
}

variable "BUDIBASE_IMAGE_URL" {
    type        = string
    description = "The URL of the Budibase image to use for the ECS container"
}


# Variables hardcoded here

variable "NAT_GATEWAY_COUNT" {
    description = "Number of NAT Gateways to create in the current environment (0-3)"
    type        = number
    default     = 1

    validation {
        condition     = var.NAT_GATEWAY_COUNT >= 0 && var.NAT_GATEWAY_COUNT <= 3
        error_message = "NAT Gateway count must be between 0 and 3."
    }
}

variable "SUBNETS_BY_ENV" {
    type        = map(list(string))
    description = "Maps a dedicated list of subnets to each of dev, stage, prod"
    default     = {
        "dev"   = ["a", "b", "c"]
        "stage" = ["d", "e", "f"]
        "prod"  = ["g", "h", "i"]   
    }
}
