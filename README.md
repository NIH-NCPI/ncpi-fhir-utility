# 🔥 NCPI FHIR Utility
<p align="center">
  <a href="https://github.com/ncpi-fhir/ncpi-fhir-utility/blob/master/LICENSE"><img src="https://img.shields.io/github/license/ncpi-fhir/ncpi-fhir-utility.svg?style=for-the-badge"></a>
  <a href="https://circleci.com/gh/ncpi-fhir/ncpi-fhir-utility"><img src="https://img.shields.io/circleci/project/github/ncpi-fhir/ncpi-fhir-utility.svg?style=for-the-badge"></a>
</p>

A small Python library and CLI that aids in FHIR model development.

Some features are:

1. **Validation** - Provides a more user-friendly interface to the Java-based [HL7 FHIR IG Publisher](https://confluence.hl7.org/display/FHIR/IG+Publisher+Documentation). It also adds additional validation to ensure consistency among FHIR resource file names and payloads.
2. **Model publication** - Submits a directory of FHIR resources to a FHIR server.
3. **JSON/XML conversion** - Converts FHIR resource payloads between JSON and XML.

## Installation

### Prerequisite

Make sure you have Docker CE installed: https://docs.docker.com/install/

Docker is needed because the `fhirutil` CLI executes the model validation
inside a Docker container which runs the HL7 FHIR IG Publisher.

1. Setup a Python virtual environment

```bash
$ python3 -m venv venv
$ source ./venv/bin/activate
```

2. Install the library with pip

```bash
$ pip install git+https://github.com/ncpi-fhir/ncpi-fhir-utility.git
```
Test the installation by running the CLI: `fhirutil -h`. You should see
something that contains:
```
Usage: fhirutil [OPTIONS] COMMAND [ARGS]...

  A CLI utility for validating FHIR Profiles and Resources
```

## Model Validation

The `fhirutil` validation feature is meant to be used on a folder which follows
the required structure and content of a FHIR ImplementationGuide. The
phrase "FHIR model" refers to the conformance resources in the
ImplementationGuide.

### Setup

Copy a FHIR resource into the test IG
```shell
cp tests/data/profiles/valid/StructureDefinition-participant.json tests/data/site_root/input/resources/profiles
```

### Validate
You can use the CLI in two different ways to aid in validating your model:

1. Use the CLI to do all steps of validation:

- Add necessary configuration for the FHIR resources in your model to the
  ImplementationGuide FHIR resource
- Validate file names and FHIR resource IDs according to naming standards
- Invoke the Dockerized version of the IG Publisher to validate the model

```shell
$ fhirutil validate tests/data/site_root/ig.ini --publisher_opts='-tx n/a'
```

2. Use the CLI along with the native IG Publisher:

- Add necessary configuration for the FHIR resources in your model to the
  ImplementationGuide FHIR resource
- Validate file names and FHIR resource IDs according to naming standards
- Run the IG Publisher Java jar natively on your machine to validate the model

```shell
$ fhirutil add ./tests/data/site_root/input/resources
$ java -jar org.hl7.fhir.publisher.jar -ig site_root/ig.ini -tx n/a
```

This method is a bit faster since it's running the IG Publisher directly and does not need to spin up a Docker container, but it means that you must first install the IG Publisher yourself ([IG Publisher installation instructions](https://confluence.hl7.org/display/FHIR/IG+Publisher+Documentation#IGPublisherDocumentation-Installing)).

### Results
The CLI will log output to the screen and tell you whether validation succeeded
or failed. You can view detailed validation results from the IG Publisher at
`./tests/data/site_root/output/qa.html`
