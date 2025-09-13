#!/usr/bin/env python3
"""
Setup script for canopyctl - A tool for managing and inspecting Canopy configurations.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="canopyctl",
    version="0.2.0",
    author="Canopy Team",
    author_email="info@canopybmc.org",
    description="A tool for managing and inspecting Canopy configurations",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/canopybmc/canopyctl",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Tools",
        "Topic :: System :: Systems Administration",
    ],
    python_requires=">=3.8",
    install_requires=[
        # No external dependencies - uses only Python standard library
    ],
    entry_points={
        "console_scripts": [
            "canopyctl=canopyctl.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)