#!/bin/bash

# Test installation and use of the ncpi-fhir-utility package

set -eo pipefail

echo "Begin package install and usage test ..."

# Setup
echo "Setup python venv"
mkdir workspace
cd workspace
cp -r ../tests .

python3 -m venv venv
source ./venv/bin/activate
pip install --upgrade pip

# If not running on CircleCI get the branch we're on
if [[ -z $CIRCLE_BRANCH ]];
then
    CIRCLE_BRANCH=$(git branch | sed -n -e 's/^\* \(.*\)/\1/p')
else
    RUN_LOCAL="1"
fi

# Test
echo "Install ncpi_fhir_utility, using branch $CIRCLE_BRANCH"
pip install "git+https://git@github.com/ncpi-fhir/ncpi-fhir-utility.git@$CIRCLE_BRANCH"

cp tests/data/profiles/valid/StructureDefinition-participant.json \
tests/data/site_root/input/resources/profiles
fhirutil validate tests/data/site_root/ig.ini --publisher_opts="-tx n/a" --clear_output

# Clean up & reset
if [[ -z $RUN_LOCAL ]];
then
    echo "Clean up"
    cd ..
    rm -rf workspace
fi

echo "✅ Complete package installation tests"
