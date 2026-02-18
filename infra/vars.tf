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

variable "CODE_BUCKET" {
  type        = string
  description = "The name of the S3 bucket containing code for Lambdas, etc."
}

variable "LAMBDA_CREATE_SERVICE_VERSION" {
  type        = string
  description = "The version of the create_budibase_service Lambda code to deploy"
}

variable "LAMBDA_DESTROY_SERVICE_VERSION" {
  type        = string
  description = "The version of the destroy_budibase_service Lambda code to deploy"
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

  validation {
    condition     = floor(var.NAT_GATEWAY_COUNT) == var.NAT_GATEWAY_COUNT
    error_message = "NAT Gateway count must be an integer."
  }
}

variable "BUDIBASE_TASK_COUNT" {
  description = "Number of Budibase Fargate tasks to run in the current environment"
  type        = number
  default     = 0

  validation {
    condition     = var.BUDIBASE_TASK_COUNT > -1
    error_message = "Budibase task count must be 0 or more."
  }

  validation {
    condition     = floor(var.BUDIBASE_TASK_COUNT) == var.BUDIBASE_TASK_COUNT
    error_message = "Budibase task count must be an integer."
  }
}

variable "SUBNETS_BY_ENV" {
  type        = map(list(string))
  description = "Maps a dedicated list of subnets to each of dev, stage, prod"
  default = {
    "dev"   = ["a", "b", "c"]
    "stage" = ["d", "e", "f"]
    "prod"  = ["g", "h", "i"]
  }
}
