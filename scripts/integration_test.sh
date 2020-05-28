#!/bin/bash

# Run the integration tests

# Usage ./scripts/integration_test.sh

set -eo pipefail

echo "✔ Begin integration tests ..."

DOCKER_IMAGE='kidsfirstdrc/smilecdr:test'
DOCKER_CONTAINER='fhir-test-server'
FHIR_API=${FHIR_API:-'http://localhost:8000'}
FHIR_USER=${FHIR_USER:-admin}
FHIR_PW=${FHIR_PW:-password}

# -- Dockerhub login --
docker login -u kidsfirstdrc -p $DOCKER_HUB_PW

# -- Run test server --
EXISTS=$(docker container ls -q -f name=$DOCKER_CONTAINER)
if [ ! "$EXISTS" ]; then
    echo "Begin deploying test server ..."
    docker run -d --rm --name "$DOCKER_CONTAINER" -p 8000:8000 -p 9100:9100 "$DOCKER_IMAGE"
    # Wait for server to come up
    until docker container logs "$DOCKER_CONTAINER" 2>&1 | grep "up and running"
    do
        echo -n "."
        sleep 2
    done
fi

# -- Setup for tests ---
if [[ ! -d venv ]];
then
    ./scripts/build.sh
    pip install -r dev-requirements.txt
fi
source ./venv/bin/activate

# -- Run tests --

# 1. Publish FHIR model
fhirutil publish tests/data/extensions/valid \
--base_url="$FHIR_API" --username="$FHIR_USER" --password="$FHIR_PW"

fhirutil publish tests/data/profiles/valid \
--base_url="$FHIR_API" --username="$FHIR_USER" --password="$FHIR_PW"

fhirutil publish tests/data/examples/valid \
--base_url="$FHIR_API" --username="$FHIR_USER" --password="$FHIR_PW"

echo "✅ Finished integration tests!"
