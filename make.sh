#!/bin/bash

RM="rm -rfd"
RED='\033[0;31m'
NC='\033[0m'
GREEN='\033[0;32m'

function clean_kubernetes() {
    # Clean kubernetes
    # ENVIRONMENT VARIABLES:
    #   FORCE: true/false - Force deletion of pods and jobs

    # Check Arguments
    if [ -z ${FORCE+x} ]; then FORCE='false'; fi

    kubectl delete -f deploy/kubernetes/ --force=${FORCE}
    kubectl delete pods --all --force=${FORCE}
    kubectl delete jobs --all --force=${FORCE}
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
    for folder_cryosparc in "venv" "__pycache__" ".ruff_cache" ".pytest_cache" ".cache"; do
        find . -type d -iname "${folder_cryosparc}" | xargs ${RM}
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

    # Check Arguments
    if [ -z ${ZIP_NAME+x} ]; then ZIP_NAME='cryosparc.zip'; fi

    folder_name="${ZIP_NAME[@]/.zip/}"
    folder_cryosparc="~/repos/${folder_name}"
    folder_repos="~/repos/"
    zip_remote_filepath="~/repos/${ZIP_NAME}"

    # Clean remote directory
    ssh osiris_lapes "if [ -d ${folder_cryosparc} ]; then rm -rfd ${folder_cryosparc}; fi" && printf "${GREEN}Cleaned remote directory${NC}\n"

    # Send zip
    scp "${ZIP_NAME}" "osiris_lapes:${folder_repos}" && printf "${GREEN}Sent zip${NC}\n"

    # Unzip
    ssh osiris_lapes "unzip ${zip_remote_filepath} -d ${folder_cryosparc}" && printf "${GREEN}Unzipped${NC}\n" || die "Failed to unzip"

    # Remove zip locally and remotely
    ssh osiris_lapes "rm ${zip_remote_filepath}" && printf "${GREEN}Removed zip remotely${NC}\n"
    rm ${ZIP_NAME} && printf "${GREEN}Removed zip locally${NC}\n"
}

function build_push_cryosparc_on_remote() {
    # Build and push cryosparc on remote server

    folder_cryosparc="~/repos/cryosparc"

    # Build and push cryosparc master image
    ssh osiris_lapes "cd ${folder_cryosparc} && docker build -t cerit.io/cerit/cryosparc:master-v0.2 -f deploy/docker/Dockerfile_cryosparc_mw_v2 . && docker push cerit.io/cerit/cryosparc:master-v0.2" && printf "${GREEN}Build and push cryosparc${NC}\n"
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
