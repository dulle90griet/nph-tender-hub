#!/usr/bin/env bash

# Fn: Escape special characters in strings for use in sed substitutions
safe_escape () {
    printf '%s\n' "$1" | sed 's/[&/\]/\\&/g'
}

# Fn: Generate the target .tf using the provided associative array
generate () {
    # Retrieve args
    TARGET_FILE="$1"
    declare -n VALS_REF=$2

    # Build the sed substitution command
    CMD="sed"
    for KEY in "${!VALS_REF[@]}"
    do
        CMD="${CMD} -e \"s/\\\${tfenv.${KEY}}/${VALS_REF[$KEY]}/g\""
    done
    CMD="${CMD} \"${SCRIPT_DIR}/${TARGET_FILE}.tf.template\""
    CMD="${CMD} > \"${SCRIPT_DIR}/${TARGET_FILE}.tf\""

    # Evaluate constructed command
    eval "$CMD"
}


# Get the script's directory path
SCRIPT_DIR=$(dirname "$(readlink -f "$0")") 

# Export .tfenv's values into the environment
source "${SCRIPT_DIR}/.tfenv"

# Extract the list of variable names defined in .tfenv
VARS=( $(cat "${SCRIPT_DIR}/.tfenv" | grep -Po "\b(.+)(?==)") )

# Zip names and values together into an associative array
declare -A VALS
for VAR in "${VARS[@]}"
do
    VALS+=( ["$VAR"]="$( eval "safe_escape \"\$${VAR}\"" )" )
done

# Generate the .tfs
generate "backend" VALS
echo "backend.tf generated using values defined in .tfenv file."
generate "vars" VALS
echo "vars.tf generated using values defined in .tfenv file."
