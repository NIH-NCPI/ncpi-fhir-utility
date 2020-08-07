"""
General module for methods called by the ncpi_fhir_utility.cli
    - Validation of FHIR data model using IG publisher
    - Remove resource configuration from IG
    - Publish FHIR data model (conformance and example resources)
      to Simplifier.net
"""
from collections import defaultdict
from copy import deepcopy
from pprint import pformat
import os
import logging
import subprocess
from shutil import rmtree
from configparser import ConfigParser

from requests.auth import HTTPBasicAuth

from ncpi_fhir_utility.utils import read_json, write_json, camel_to_snake
from ncpi_fhir_utility import loader
from ncpi_fhir_utility.client import FhirApiClient
from ncpi_fhir_utility.config import (
    RUN_IG_PUBLISHER_SCRIPT,
    CONFORMANCE_RESOURCES,
    RESOURCE_SUBMISSION_ORDER,
)

RESOURCE_ID_DELIM = "-"
FILENAME_DELIM = RESOURCE_ID_DELIM
logger = logging.getLogger(__name__)


def validate(
    ig_control_filepath,
    clear_output=False,
    publisher_opts="",
    refresh_publisher=True,
):
    """
    Validate the FHIR data model (FHIR conformance and example resources)

    Run the HL7 FHIR implementation guide (IG) publisher in a Docker container
    to validate conformance resources and any example resources against the
    conformance resources.

    See https://confluence.hl7.org/display/FHIR/IG+Publisher+Documentation

    Validation fails if any of the following are true:
        - The publisher returns a non-zero exit code
        - QA report contains errors with the FHIR resources.
        - Any one of the resource files fail model validation in
        _custom_validate

    IG build errors are ignored since this method only validates the data
    model

    :param ig_control_filepath: Path to the implementation guide control file
    :type ig_control_filepath: str
    :param clear_output: Whether to clear all generated output before
    validating
    :type clear_output: boolean
    :param publisher_opts: IG publisher command line options forwarded directly
    to the publisher CLI
    :type publisher_opts: str
    :param refresh_publisher: A flag specifying whether to pull down the IG
    publisher Docker image from the remote Docker repository before running
    the IG publisher
    :type refresh_publisher: boolean
    """
    logger.info("Begin validation of FHIR data model")
    ig_control_filepath = os.path.abspath(
        os.path.expanduser(ig_control_filepath)
    )

    # Clear previously generated output
    if clear_output:
        clear_ig_output(ig_control_filepath)

    # Read in ig resource file
    ig_resource_dict = _load_ig_resource_dict(ig_control_filepath)

    # Collect resource filepaths
    resource_dicts = []
    site_root = os.path.dirname(ig_control_filepath)
    ig = ig_resource_dict["content"]
    for param in ig.get("definition", {}).get("parameter", []):
        if param.get("code") != "path-resource":
            continue
        resource_dicts.extend(
            loader.load_resources(os.path.join(site_root, param.get("value")))
        )

    # Validate and add resource to IG configuration
    _custom_validate(resource_dicts)

    # Add entry to IG configuration
    _update_ig_config(resource_dicts, ig_resource_dict, add=True)

    # Do the standard HL7 FHIR validation via the IG Publisher
    _fhir_validate(ig_control_filepath, publisher_opts, refresh_publisher)

    logger.info("End validation of FHIR data model")


def clear_ig_output(ig_control_filepath):
    """
    Delete all of the output dirs generated by the IG publisher

    :param ig_control_filepath: Path to the implementation guide control file
    :type ig_control_filepath: str
    """
    site_root = os.path.dirname(ig_control_filepath)
    for dir in ["output", "temp", "template", "input-cache"]:
        p = os.path.join(site_root, dir)
        if os.path.exists(p):
            logger.info(f"Clearing all previously generated output at: {p}")
            rmtree(p)


def update_ig_config(data_path, ig_control_filepath, add=True, rm_file=False):
    """
    Add/remove the configuration entries to/from IG resource file for all
    resources in data_path.

    Optional - delete the resource file(s). Only applies if add=False.

    When a new resource file is added to the IG it will not be picked up for
    validation or site generation by the IG publisher unless the expected
    configuration for that resource is present.

    :param data_path: Path to directory or file containing resource(s) to
    remove from the IG configuration
    :param ig_control_filepath: Path to the implementation guide control file
    :type ig_control_filepath: str
    :param add: Whether to add the configuration versus remove it
    :type add: bool
    :param rm_file: Whether to delete the resource file(s). Only applies if
    add=False
    :type rm_file: bool
    """
    # Load resource dicts
    resource_dicts = loader.load_resources(data_path)
    # Load IG resource dict
    ig_resource_dict = deepcopy(_load_ig_resource_dict(ig_control_filepath))
    # Validate and add resource to IG configuration
    _custom_validate(resource_dicts)

    # Update the IG configuration
    _update_ig_config(resource_dicts, ig_resource_dict)


def publish_to_server(
    resource_file_or_dir,
    base_url,
    username=None,
    password=None,
    fhir_version=None,
    submission_order=RESOURCE_SUBMISSION_ORDER,
):
    """
    Push FHIR resources to a FHIR server

    Delete the resources if they exist on the server
    PUT any resources that have an `id` attribute defined
    POST any resources that do not have an `id` attribute defined

    :param resource_file_or_dir: path to a directory containing FHIR resource
    files or path to a single resource file
    :type resource_file_or_dir: str
    :param resource_type: directory containing FHIR resource files
    :type resource_type: str
    :param username: Server account username
    :type username: str
    :param password: Server account password
    :type password: str
    :param fhir_version: FHIR version number
    :type fhir_version: str
    """
    logger.info(
        f"Begin publishing resources in {resource_file_or_dir} to {base_url}"
    )

    if username and password:
        auth = HTTPBasicAuth(username, password)
    else:
        auth = None

    client = FhirApiClient(
        base_url=base_url, auth=auth, fhir_version=fhir_version
    )
    resources = loader.load_resources(resource_file_or_dir)

    # Re-order resources according to submission order
    resources_by_type = defaultdict(list)
    for r_dict in resources:
        resources_by_type[r_dict["resource_type"]].append(r_dict)
    resources = []
    for r_type in submission_order:
        resources.extend(resources_by_type.pop(r_type, []))
    for r_type, remaining in resources_by_type.items():
        resources.extend(remaining)

    # Delete existing resources
    for r_dict in resources:
        r = r_dict["content"]
        if "url" in r:
            success = client.delete_all(
                f'{base_url}/{r["resourceType"]}', params={"url": r["url"]}
            )
        elif "id" in r:
            success, results = client.send_request(
                "delete", f'{base_url}/{r["resourceType"]}/{r["id"]}'
            )
        else:
            logger.warning(
                f'⚠️ Could not delete {r_dict["filename"]}. No way to '
                "identify the resource. Tried looking for `url` and `id` in "
                "payload."
            )

    # POST if no id is provided, PUT if id is provideds
    for r_dict in resources:
        r = r_dict["content"]
        id_ = r.get("id")
        if id_:
            success, results = client.send_request(
                "put", f'{base_url}/{r["resourceType"]}/{id_}', json=r
            )
        else:
            success, results = client.send_request(
                "post", f'{base_url}/{r["resourceType"]}', json=r
            )
        if not success:
            errors = [
                r
                for r in results["response"]["issue"]
                if r["severity"] == "error"
            ]
            raise Exception(f"Publish failed! Caused by:\n{pformat(errors)}")


def _fhir_validate(ig_control_filepath, publisher_opts, refresh_publisher):
    """
    Run the HL7 IG Publisher to do standard FHIR validation on resource files

    Called in validate

    :param ig_control_filepath: Path to the implementation guide control file
    :type ig_control_filepath: str
    :param publisher_opts: IG publisher command line options forwarded directly
    to the publisher CLI
    :type publisher_opts: str
    :param refresh_publisher: A flag specifying whether to pull down the IG
    publisher Docker image from the remote Docker repository before running
    the IG publisher
    :type refresh_publisher: boolean
    """
    # Run IG publisher to do FHIR validation
    args = [
        RUN_IG_PUBLISHER_SCRIPT,
        ig_control_filepath,
        str(int(refresh_publisher)),
    ]
    if publisher_opts:
        args.append(publisher_opts)
    subprocess.run(args, shell=False, check=True)

    # Check QA report for validation errors
    site_root = os.path.dirname(ig_control_filepath)
    qa_path = os.path.join(site_root, "output", "qa")
    qa_report = os.path.abspath(qa_path + ".html")
    logger.info(f"Checking QA report {qa_report} for validation errors")
    qa_json = read_json(qa_path + ".json")
    if qa_json.get("errs"):
        # Extract error messages from qa.txt
        errors = []
        with open(os.path.abspath(qa_path + ".txt")) as qa_txt:
            for line in qa_txt.readlines():
                ln = line.strip()
                if ln.lower().startswith("error") and (".html" not in ln):
                    errors.append(ln)
            errors = "\n".join(errors)
        raise Exception(
            f"Errors found in QA report. See {qa_report} for details:"
            f"\n\n{errors}\n"
        )


def _custom_validate(resource_dicts):
    """
    Do custom validation of a resource file in the FHIR model

    Called in validate

    Validation Rules:
    1. JSON paylod must have an `id` attribute populated with a value which
       adheres to kebab-case
    2. StructureDefinition must have `url` defined
    3. StructureDefinition.id = StructureDefinition.url.split('/')[-1]
    4. File name must follow format <resource type>-<resource id>
    """
    for rd in resource_dicts:
        res = rd["content"]
        # Check if id is present
        rid = res.get("id")
        if not rid:
            raise KeyError(
                "All resources must have an `id` attribute. Resource file: "
                f'{rd["filepath"]} is missing `id` or `id` is null.'
            )
        # If StructureDefinition check that URL is valid
        if res["resourceType"] == "StructureDefinition":
            if not res.get("url"):
                raise KeyError(
                    "All StructureDefinition resources must have a `url`. "
                    f'Resource file: {rd["filepath"]} is missing `url` or '
                    "`url` is null."
                )
            url_parts = res.get("url").split("/")
            if res["id"] != url_parts[-1]:
                raise ValueError(
                    "Invalid value for `url` in StructureDefinition: "
                    f'{rd["filepath"]}. Value should be: '
                    f'{"/".join(url_parts + [res["id"]])}'
                )

        # Try to check if id follows kebab-case (won't be perfect)
        expected_id = camel_to_snake(rid).replace("_", "-")
        if rid != expected_id:
            raise ValueError(
                "Resource id must adhere to kebab-case (lowercase with "
                f'hyphens between tokens). The `id` "{rid}" in '
                f'{rd["filepath"]} should be: {expected_id}'
            )
        # Check filename
        filename, ext = os.path.splitext(os.path.split(rd["filepath"])[-1])
        rtype = rd.get("resource_type")
        expected_filename = f"{rtype}-{rid}"
        if filename != expected_filename:
            raise ValueError(
                "Resource file names must follow pattern: "
                f"<resource type>-<resource id>.json. File {filename}{ext} "
                f"should be: {expected_filename}{ext}"
            )
        logger.info(f"☑️ Initial validation passed for resource {filename+ext}")


def _update_ig_config(
    resource_dicts, ig_resource_dict, add=True, rm_file=False
):
    """
    Helper for update_ig_config
    """
    # Collect resource ids from the input set of resources
    resource_set = {
        f'{r["content"]["resourceType"]}/{r["content"]["id"]}'
        for r in resource_dicts
    }
    # Reformat IG resource list into a dict so its easier to update
    ig_resource = ig_resource_dict["content"]
    resources_dict = {}
    for r in ig_resource["definition"]["resource"]:
        # Only include resources from IG config that have corresponding filess
        # Old IG entries will be discarded
        key = r["reference"]["reference"]
        if key in resource_set:
            resources_dict[key] = r
        else:
            logger.info(f"🔥 Removing old entry {key} from IG")

    for rd in resource_dicts:
        if rd["resource_type"] == "ImplementationGuide":
            continue

        # Create the config entry
        entry = _create_resource_config(rd)

        # Add/remove configuration entries
        if add:
            resources_dict[entry["reference"]["reference"]] = entry
        else:
            del rd[entry["reference"]["reference"]]
            if rm_file:
                os.rmfile(rd["filepath"])
                logger.info(f'🗑 Deleted resource file {rd["filepath"]}')

        logger.info(f'☑️ Added IG configuration for {rd["filename"]}')

    # Format resource dict back to original list
    ig_resource["definition"]["resource"] = [
        resources_dict[k] for k in resources_dict
    ]
    write_json(
        ig_resource_dict["content"], ig_resource_dict["filepath"], indent=2
    )


def _create_resource_config(resource_dict):
    """
    Create the expected IG configuration entry for a resource

    :param resource_dict: The resource payload from which a config entry will
    be created. See ncpi_fhir_utility.loader.load_resources.
    :type resource_dict: dict
    :returns: IG config entry for the resource
    """
    rid = resource_dict["content"].get("id")
    rtype = resource_dict["content"].get("resourceType")
    suffix = ""

    if rtype in CONFORMANCE_RESOURCES:
        is_example = False
        base = resource_dict["content"].get("baseDefinition")
        if base:
            base = base.split("/")[-1]
            suffix = f", Base: {base}"
    else:
        is_example = True
        profiles = ",".join(
            [
                p.split("/")[-1]
                for p in resource_dict["content"]
                .get("meta", {})
                .get("profile", [])
            ]
        )
        if profiles:
            suffix = f", Profiles: {profiles}"

    return {
        "reference": {"reference": f"{rtype}/{rid}"},
        "name": f"NCPI {rtype}/{rid}",
        "description": f"NCPI {rtype} {rid}{suffix}",
        "exampleBoolean": is_example,
    }


def _load_ig_resource_dict(ig_control_filepath):
    """
    Load IG resource JSON into a dict

    Find the location of the IG resource file from the ig control file first

    :param ig_control_filepath: Path to the implementation guide control file
    :type ig_control_filepath: str
    :returns: IG resource dict
    """
    # Read in ig control file
    ig_control_filepath = os.path.abspath(
        os.path.expanduser(ig_control_filepath)
    )
    ig_config = ConfigParser()
    ig_config.read(ig_control_filepath)

    # Read in ig resource file
    ig_filepath = os.path.join(
        os.path.split(ig_control_filepath)[0], dict(ig_config["IG"]).get("ig")
    )
    return loader.load_resources(ig_filepath)[0]
