import logging
import os


def fhir_version_name(fhir_version):
    """
    Get the name of a particular FHIR version number

    :param: fhir_version
    :type: str

    :returns: str
    """
    major_version = int(fhir_version.split(".")[0])

    if major_version < 3:
        return "dstu2"
    elif (major_version >= 3) and (major_version < 4):
        return "stu3"
    elif (major_version >= 4) and (major_version < 5):
        return "r4"
    else:
        raise Exception(
            f"Invalid fhir version supplied: {fhir_version}! No name exists "
            "for the supplied fhir version."
        )


DEFAULT_LOG_LEVEL = logging.DEBUG

FHIR_VERSION = "4.0.0"
FHIR_VERSION_NAME = fhir_version_name(FHIR_VERSION)
CONFORMANCE_RESOURCES = {
    "CapabilityStatement",
    "StructureDefinition",
    "CodeSystem",
    "ValueSet",
    "ImplementationGuide",
    "SearchParameter",
    "MessageDefinition",
    "OperationDefinition",
    "CompartmentDefinition",
    "StructureMap",
    "GraphDefinition",
    "ExampleScenario",
}

RESOURCE_SUBMISSION_ORDER = [
    "CodeSystem",
    "ValueSet",
    "StructureDefinition",
    "SearchParameter",
    "Patient",
    "ResearchSubject",
    "Specimen",
    "Practitioner",
    "Organization",
    "PractitionerRole",
    "Observation",
    "Condition",
]

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
DEFAULT_SITE_ROOT = os.path.join(os.getcwd(), "site_root")
DEFAULT_IG_CONTROL_FILE = os.path.join(DEFAULT_SITE_ROOT, "ig.ini")
SCRIPTS_DIR = os.path.join(ROOT_DIR, "scripts")
RUN_IG_PUBLISHER_SCRIPT = "run_publisher.sh"

TORINOX_DOCKER_REPO = "kidsfirstdrc/torinox"
# Map of fhir version to tuple: (Docker image tag, torinox CLI callable)
TORINOX_FHIR_VERSION_MAP = {
    "r4": ("torinox.r4-latest", "fhir4"),
    "stu3": ("torinox-latest", "fhir"),
}

OUR_URLS = "http://fhir.ncpi.io,https://fhir.ncpi.io"
