#!/usr/bin/env bash

SCRIPT_DIR=$(dirname "$(readlink -f "$0")") 

source "${SCRIPT_DIR}/.tfenv"

safe_escape () {
    printf '%s\n' "$1" | sed 's/[&/\]/\\&/g'
}

VARS=( $(cat "${SCRIPT_DIR}/.tfenv" | grep -Po "\b(.+)(?==)") )

declare -A VALS
for VAR in "${VARS[@]}"
do
    VALS+=( ["$VAR"]="$( eval "safe_escape \"\$${VAR}\"" )" )
done

generate () {
    CMD="sed"

    declare -n VALS_REF=$2

    for KEY in "${!VALS_REF[@]}"
    do
        CMD="${CMD} -e \"s/\\\${tfenv.${KEY}}/${VALS_REF[$KEY]}/g\""
    done
    CMD="${CMD} \"${SCRIPT_DIR}/${1}.tf.template\""
    CMD="${CMD} > \"${SCRIPT_DIR}/${1}.tf\""

    eval "$CMD"
}

generate backend VALS
echo "backend.tf generated using values defined in .tfenv file."
generate vars VALS
echo "vars.tf generated using values defined in .tfenv file."