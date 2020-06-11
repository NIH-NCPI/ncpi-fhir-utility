import os
from setuptools import setup, find_packages

from ncpi_fhir_utility.config import FHIR_VERSION

root_dir = os.path.dirname(os.path.abspath(__file__))
req_file = os.path.join(root_dir, "requirements.txt")
with open(req_file) as f:
    requirements = f.read().splitlines()

setup(
    name="ncpi-fhir-utility",
    use_scm_version={
        "local_scheme": "dirty-tag",
        "version_scheme": "post-release",
    },
    setup_requires=["setuptools_scm"],
    description=f"NCPI-FHIR Utility {FHIR_VERSION}",
    packages=find_packages(),
    entry_points={"console_scripts": ["fhirutil=ncpi_fhir_utility.cli:cli"]},
    include_package_data=True,
    install_requires=requirements,
    scripts=["scripts/run_publisher.sh"],
)
