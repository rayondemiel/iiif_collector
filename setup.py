#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

# Package meta-data.
NAME = 'IIIF Collector'
DESCRIPTION = "CLI package to manipulate and download IIIF images"
URL = 'https://github.com/rayondemiel/iiif_collector'
AUTHOR = 'Humeau Maxime'
REQUIRES_PYTHON = '>=3.8.0'
VERSION = "0.1.0"

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

# Where the magic happens:
setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author=AUTHOR,
    python_requires=REQUIRES_PYTHON,
    url=URL,
    packages=find_packages(exclude=('tests', '.env', 'env', 'venv',)),
    entry_points={
        'console_scripts': ['iiif-collector=iiif_collector.cli.iiif_collector:run_collect'],
    },
    include_package_data=True,
    install_requires=requirements,
    license='MIT',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'TOPIC :: SCIENTIFIC/ENGINEERING :: IMAGE PROCESSING'
    ]
)
