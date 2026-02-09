ENV=$1

terraform workspace select default \
  && terraform init -reconfigure -backend-config="envs/$ENV/backend.hcl" \
  && terraform workspace select $ENV || terraform workspace new $ENV

