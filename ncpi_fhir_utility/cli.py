"""
Entry point for the NCPI FHIR Model CLI which lets users:

- Validate FHIR model files (conformance resources, example resources)
- Convert FHIR model files between xml/json
- Push FHIR model files to FHIR server
"""
import logging
import sys

import click

from ncpi_fhir_utility import app, loader
from ncpi_fhir_utility import update_versions as uv
from ncpi_fhir_utility.config import (
    DEFAULT_IG_CONTROL_FILE,
    DEFAULT_SITE_ROOT,
    FHIR_VERSION,
    OUR_URLS,
)
from ncpi_fhir_utility.utils import setup_logger

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}

setup_logger()
logger = logging.getLogger(__name__)


def do(msg, func, *args, **kwargs):
    try:
        func(*args, **kwargs)
    except Exception as e:
        logger.exception(str(e))
        logger.info(f"❌ {msg} failed!")
        sys.exit(1)
    else:
        logger.info(f"✅ {msg} succeeded!")


@click.group(context_settings=CONTEXT_SETTINGS)
def cli():
    """
    A CLI utility for validating FHIR Profiles and Resources
    """
    pass


@cli.command()
@click.option("--password", "pw", help="Client secret or user password")
@click.option("--username", "user", help="Client id or username")
@click.option(
    "--base_url",
    type=str,
    show_default=True,
    default="http://localhost:8000",
    help="URL to FHIR server where resources will be pushed",
)
@click.argument(
    "resource_file_or_dir",
    type=click.Path(exists=True, file_okay=True, dir_okay=True),
)
def publish(resource_file_or_dir, base_url, user, pw):
    """
    Push FHIR model files to FHIR server. Default use of this method is to
    push FHIR model files to the Simplifier FHIR server configured in
    ncpi_fhir_utility.config

    \b
        Arguments:
            \b
            resource_dir - A directory containing the FHIR resource files to '
            'publish to the Simplifier project
    """
    m = "Publish"
    do(m, app.publish_to_server, resource_file_or_dir, base_url, user, pw)


@click.command()
@click.option(
    "--no_refresh_publisher",
    is_flag=True,
    help="If present, the IG publisher Docker image "
    "will not be pulled from the remote Docker repository. This allows "
    "a local IG publisher Docker image to be used if desired.",
)
@click.option(
    "--publisher_opts",
    help="A string containing command line options accepted by the "
    "IG publisher. See https://confluence.hl7.org/display/"
    "FHIR/IG+Publisher+Documentation for more details on available "
    "options. These will be passed directly to the publisher JAR",
)
@click.option(
    "--clear_output",
    is_flag=True,
    help="Whether to clear all generated output before validating",
)
@click.argument(
    "ig_control_filepath",
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
)
def validate(
    ig_control_filepath, clear_output, publisher_opts, no_refresh_publisher
):
    """
    Validate FHIR conformance resources and validate example FHIR resources
    against the conformance resources by running the HL7 FHIR implementation
    guide publisher.

    See https://confluence.hl7.org/display/FHIR/IG+Publisher+Documentation

    \b
        Arguments:
            \b
            ig_control_filepath - Path to the implementation guide control
            file. The directory of this file should be the implementation guide
            site root directory containing all of the content needed to build
            the site
    """
    m = "Validation"
    do(
        m,
        app.validate,
        ig_control_filepath,
        clear_output,
        publisher_opts,
        refresh_publisher=(not no_refresh_publisher),
    )


@click.command()
@click.option(
    "--fhir_version",
    default=FHIR_VERSION,
    show_default=True,
    help="FHIR Version",
)
@click.option(
    "--format",
    type=click.Choice(["json", "xml"]),
    help="The format to convert to",
)
@click.argument(
    "data_path", type=click.Path(exists=True, file_okay=True, dir_okay=True)
)
def convert(data_path, format, fhir_version):
    """
    Convenience method to convert a FHIR resource file JSON -> XML or
    XML -> JSON and write results to a file.

    The file will have the same name and be stored in the same directory as the
    original file. It's extension will be what was provided in --format.

    \b
        Arguments:
            \b
            data_path - A directory containing the FHIR profiles or resources
            to format or a filepath to a single profile or resource.
    """
    m = f"Converting {data_path} to {format} using FHIR version {fhir_version}"
    do(m, loader.fhir_format_all, data_path, format, fhir_version)


@click.command()
@click.option(
    "--ig_control_file",
    help="Path to the implementation guide control file.",
    default=DEFAULT_IG_CONTROL_FILE,
    show_default=True,
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
)
@click.argument(
    "data_path", type=click.Path(exists=True, file_okay=True, dir_okay=True)
)
def add(data_path, ig_control_file):
    """
    Convenience method to add the necessary configuration for the resource(s)
    to the IG configuration so that the resource is included in the
    generated IG site.

    NOTE
    The resource file, `data_path`, must already be in the IG site root. This
    CLI command does not move the file into the site root.

    \b
        Arguments:
            \b
            data_path - A directory or file containing the FHIR resource
            file(s)
    """
    m = f"Add {data_path} to IG"
    do(m, app.update_ig_config, data_path, ig_control_file)


@click.command()
@click.option(
    "--site_root",
    default=DEFAULT_SITE_ROOT,
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Path of site_root dir",
)
@click.option(
    "--our_urls",
    default=OUR_URLS,
    help="Comma-separated resource URLs that we control",
)
@click.argument("new_version")
def update_versions(site_root, new_version, our_urls):
    """
    Update the version fields for all of our resources with NEW_VERSION.
    """
    m = f"Updating {site_root} to {new_version}"
    do(m, uv.run, site_root, new_version, our_urls)


cli.add_command(publish)
cli.add_command(validate)
cli.add_command(convert)
cli.add_command(add)
cli.add_command(update_versions)
