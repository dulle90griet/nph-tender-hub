#!/usr/bin/env bash

SCRIPT_DIR=$(dirname "$(readlink -f "$0")") 

source "${SCRIPT_DIR}/.tfenv"

safe_escape () {
    printf '%s\n' "$1" | sed 's/[&/\]/\\&/g'
}
TF_AWS_REGION_ESC=$(safe_escape "$TF_AWS_REGION")
TF_STATE_BUCKET_ESC=$(safe_escape "$TF_STATE_BUCKET")
TF_STATE_KEY_ESC=$(safe_escape "$TF_STATE_KEY")

sed -e "s/\${var.AWS_REGION}/${TF_AWS_REGION_ESC}/g" \
    -e "s/\${var.STATE_BUCKET_NAME}/${TF_STATE_BUCKET_ESC}/g" \
    -e "s/\${var.STATE_KEY}/${TF_STATE_KEY_ESC}/g" \
    "${SCRIPT_DIR}/backend.tf.template" \
    > "${SCRIPT_DIR}/backend.tf"
 
 echo "backend.tf generated using values stored in .tfenv file."