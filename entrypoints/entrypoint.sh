#!/bin/bash
# Inspiration src: https://github.com/slaclab/cryosparc-docker/blob/master/cryosparc-server.sh

CRYOSPARC_MASTER_DIR=${CRYOSPARC_MASTER_DIR:-"/opt/cryosparc_master"}
CRYOSPARC_WORKER_DIR=${CRYOSPARC_WORKER_DIR:-"/opt/cryosparc_worker"}

function start_master() {
    # Start master

    source ${CRYOSPARC_MASTER_DIR}/config.sh

    CRYOSPARC_MASTER_DIR=${CRYOSPARC_MASTER_DIR:-"/opt/cryosparc_master"}
    CRYOSPARC_WORKER_DIR=${CRYOSPARC_WORKER_DIR:-"/opt/cryosparc_worker"}
    export PATH=${CRYOSPARC_MASTER_DIR}/bin:${CRYOSPARC_WORKER_DIR}/bin:${CRYOSPARC_MASTER_DIR}/deps/anaconda/bin/:$PATH

    export CRYOSPARC_MASTER_HOSTNAME=${CRYOSPARC_MASTER_HOSTNAME:-$(hostname -s)}
    echo "setting CRYOSPARC_MASTER_HOSTNAME=${CRYOSPARC_MASTER_HOSTNAME}"
    echo "Starting cryosparc master..."

    cd ${CRYOSPARC_MASTER_DIR}
    cryosparcm start || cryosparcm restart
    cd -

    echo "Success starting cryosparc master!"
}

function create_user() {
    # Create user

    email="a@a.com"
    username="a"
    password="a"
    firstname="John"
    lastname="Doe"

    cd ${CRYOSPARC_MASTER_DIR}/entrypoints/
    ../bin/cryosparcm createuser \
        --email ${email} \
        --password ${password} \
        --username ${username} \
        --firstname ${firstname} \
        --lastname ${lastname}
    cd -
}

function start_worker() {
    # Start worker

    source ${CRYOSPARC_WORKER_DIR}/config.sh
    echo "Starting cryosparc worker for ${CRYOSPARC_MASTER_HOSTNAME}..."
    export SSDPATH=/mnt/ssd_path
    mkdir -p ${SSDPATH}
    #    export CRYOSPARC_BASE_PORT=8080

    export CRYOSPARC_MASTER_HOSTNAME=${CRYOSPARC_MASTER_HOSTNAME:-$(hostname -s)}
    echo "setting CRYOSPARC_MASTER_HOSTNAME=${CRYOSPARC_MASTER_HOSTNAME}"

    cd ${CRYOSPARC_WORKER_DIR}
    ${CRYOSPARC_WORKER_DIR}/bin/cryosparcw connect \
        --worker ${CRYOSPARC_MASTER_HOSTNAME} \
        --master ${CRYOSPARC_MASTER_HOSTNAME} \
        --port 8080 \
        --ssdpath ${SSDPATH}/
    #    ${CRYOSPARC_WORKER_DIR}/bin/cryosparcw connect \
    #    --worker localhost \
    #    --master localhost \
    #    --port 8080 \
    #    --ssdpath ${SSDPATH}/
    #    echo "Success starting cryosparc worker!"
    cd -
}

function heartbeat() {
    # Keep container alive
    while true; do
        sleep 1000
    done
}

##############################################
# Helper functions
##############################################
function help() {
    # Print usage on stdout
    echo "Example usage:"
    echo "    ENV_KEY=ENV_VALUE ${BASH_SOURCE[0]} <function>"

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
    RED='\033[0;31m'
    NC='\033[0m' # No Color
    help
    printf "${RED}ERROR: $1${NC}\n"
    exit 1
}

function main() {
    # Main function: Call other functions based on input arguments, this is called automatically
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
