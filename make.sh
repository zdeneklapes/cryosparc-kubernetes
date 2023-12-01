#!/bin/bash

RM="rm -rfd"
RED='\033[0;31m'
NC='\033[0m'
GREEN='\033[0;32m'

function clean_kubernetes() {
    kubectl delete -f deploy/kubernetes/
    kubectl delete pods --all -f
    kubectl delete jobs --all -f
}

function docker_show_ipaddress() {
    # Show ip address of running containers
    for docker_container in $(docker ps -aq); do
        CMD1="$(docker ps -a | grep "${docker_container}" | grep --invert-match "Exited\|Created" | awk '{print $2}'): "
        if [ ${CMD1} != ": " ]; then
            printf "${CMD1}"
            printf "$(docker inspect ${docker_container} | grep "IPAddress" | tail -n 1)\n"
        fi
    done
}
function clean() {
    # Clean project
    ${RM} *.zip
    # Folders
    for folder in "venv" "__pycache__" ".ruff_cache" ".pytest_cache" ".cache"; do
        find . -type d -iname "${folder}" | xargs ${RM}
    done
    # Files
    for file in ".DS_Store" "tags" "db.sqlite3" "*.png" "*.zip" "*.log"; do
        find . -type f -iname "${file}" | xargs ${RM}
    done
}

function tags() {
    # Create tags and cscope
    ctags -R .
    cscope -Rb
}

function pack() {
    # Pack project
    # ENVIRONMENT VARIABLES:
    #   ZIP_NAME: Name of the zip file

    # check if zip name is set
    if [ -z ${ZIP_NAME+x} ]; then ZIP_NAME='cryosparc.zip'; fi

    clean
    zip -r "${ZIP_NAME}" \
        deploy \
        src \
        entrypoints \
        Dockerfile \
        make.sh \
        requirements.txt
}

function send() {
    # Send zipped project to osiris using scp
    # ENVIRONMENT VARIABLES:
    #   ZIP_NAME: Name of the zip file
    #   VPS_URI: URI of the remote server

    # Check Arguments
    if [ -z ${ZIP_NAME+x} ]; then ZIP_NAME='cryosparc.zip'; fi
    if [ -z ${VPS_URI+x} ]; then VPS_URI='osiris_lapes:/home/lapes/repos'; fi

    folder="~/repos/cryosparc"
    zip_remote_filepath="~/repos/${ZIP_NAME}"

    # Clean remote directory
    ssh osiris_lapes "rm -rfd ${folder}" && printf "${GREEN}Cleaned remote directory${NC}\n"

    # Send zip
    scp "${ZIP_NAME}" "${VPS_URI}" && printf "${GREEN}Sent zip${NC}\n" || die "Failed to send zip"

    # Unzip
    ssh osiris_lapes "unzip /home/lapes/repos/cryosparc.zip -d /home/lapes/repos/cryosparc" && printf "${GREEN}Unzipped${NC}\n"

    # Remove zip locally and remotely
    ssh osiris_lapes "rm -rfd ${zip_remote_filepath}" && printf "${GREEN}Removed zip remotely${NC}\n"
    rm ${ZIP_NAME} && printf "${GREEN}Removed zip locally${NC}\n"
}

function help() {
    # Print usage on stdout
    echo "Available functions:"
    for file in ${BASH_SOURCE[0]}; do
        function_names=$(cat ${file} | grep -E "(\ *)function\ +.*\(\)\ *\{" | sed -E "s/\ *function\ +//" | sed -E "s/\ *\(\)\ *\{\ *//")
        for func_name in ${function_names[@]}; do
            printf "    $func_name\n"
            awk "/function ${func_name}()/ { flag = 1 }; flag && /^\ +#/ { print \"        \" \$0 }; flag && !/^\ +#/ && !/function ${func_name}()/  { print "\n"; exit }" ${file}
        done
    done

}

function usage() {
    # Print usage on stdout
    help
}

function die() {
    # Print error message on stdout and exit
    help
    printf "${RED}ERROR: $1${NC}\n"
    exit 1
}

function main() {
    # Main function: Call other functions based on input arguments
    [[ "$#" -eq 0 ]] && die "No arguments provided"
    while [ "$#" -gt 0 ]; do
        case "$1" in
        # BUG: die run even if function exists (but error occur inside function)
        *) "$1" || die "Unknown function: $1() or error occur inside function" ;;
        esac
        shift
    done
}

main "$@"
