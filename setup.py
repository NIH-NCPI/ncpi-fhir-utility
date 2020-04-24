import os
from setuptools import setup, find_packages

from ncpi_fhir_utility.config import FHIR_VERSION

root_dir = os.path.dirname(os.path.abspath(__file__))
req_file = os.path.join(root_dir, 'requirements.txt')
with open(req_file) as f:
    requirements = f.read().splitlines()

version = __import__('ncpi_fhir_utility').__version__

setup(
    name='ncpi-fhir-utility',
    version=version,
    description=f'NCPI-FHIR Utility {FHIR_VERSION}',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'fhirutil=ncpi_fhir_utility.cli:cli',
        ],
    },
    include_package_data=True,
    install_requires=requirements
)
