function prune_docker() {
    # Stop and remove all containers
    docker stop $(docker ps -aq)
    docker system prune --all --force --volumes

    # Remove all volumes: not just dangling ones
    for i in $(docker volume ls --format json | jq -r ".Name"); do
        docker volume rm -f ${i}
    done
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

function dev_docker_up() {
    source "${ENV}" set || error_exit "source \${ENV} set"
    LISTEN_PORT=${DJANGO_PORT} docker compose -f docker-compose.dev.yml down
    LISTEN_PORT=${DJANGO_PORT} docker compose -f docker-compose.dev.yml --build -d
}

function prod_docker_up() {
    # This function is used start
    source "${ENV}" set || error_exit "source \${ENV} set"
    LISTEN_PORT=${DJANGO_PORT} docker compose -f docker-compose.prod.yml down
    LISTEN_PORT=${DJANGO_PORT} docker compose -f docker-compose.prod.yml up --build -d
}

function prod_entrypoint() {
    # This function is used as entrypoint in Dockerfile.prod
    cd src || error_exit "cd"
    python3 manage.py update_groups_permissions -p
    python3 manage.py runserver 0.0.0.0:8000
    cd .. || error_exit "cd"
}

function dev_entrypoint() {
    # This function is used as entrypoint in Dockerfile.dev
    cd src || error_exit "cd"
#    FIXTURE_PATHS_AUTO_FIND=src/**/fixtures/*.json
    FIXTURE_PATHS=(
    "./accounts/fixtures/accounts.json"
    )
    python3 manage.py makemigrations
    python3 manage.py migrate
    python3 manage.py loaddata "${FIXTURE_PATHS[@]}"
    #    python3 manage.py update_groups_permissions -p
    python3 manage.py runserver 0.0.0.0:8000
    cd .. || error_exit "cd"
}
