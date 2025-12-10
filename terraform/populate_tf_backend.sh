#!/usr/bin/env bash

SCRIPT_DIR=$(dirname "$(readlink -f "$0")") 

source "${SCRIPT_DIR}/.tfenv"

safe_escape () {
    printf '%s\n' "$1" | sed 's/[&/\]/\\&/g'
}

AWS_REGION_ESC=$(safe_escape "$AWS_REGION")
STATE_BUCKET_ESC=$(safe_escape "$STATE_BUCKET")
STATE_KEY_ESC=$(safe_escape "$STATE_KEY")
PREFIX_ESC=$(safe_escape "$PREFIX")
TAGS_CLIENT_ESC=$(safe_escape "$TAGS_CLIENT")
TAGS_PROJECT_ESC=$(safe_escape "$TAGS_PROJECT")

generate () {
    sed -e "s/\${tfenv.AWS_REGION}/${AWS_REGION_ESC}/g" \
        -e "s/\${tfenv.STATE_BUCKET}/${STATE_BUCKET_ESC}/g" \
        -e "s/\${tfenv.STATE_KEY}/${STATE_KEY_ESC}/g" \
        -e "s/\${tfenv.PREFIX}/${PREFIX_ESC}/g" \
        -e "s/\${tfenv.TAGS_CLIENT}/${TAGS_CLIENT_ESC}/g" \
        -e "s/\${tfenv.TAGS_PROJECT}/${TAGS_PROJECT_ESC}/g" \
        "${SCRIPT_DIR}/$1.tf.template" \
        > "${SCRIPT_DIR}/${1}.tf"
}

generate backend
echo "backend.tf generated using values defined in .tfenv file."
generate vars
echo "vars.tf generated using values defined in .tfenv file."