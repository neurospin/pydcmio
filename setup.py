#! /usr/bin/env python
##########################################################################
# NSAp - Copyright (C) CEA, 2015
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
from setuptools import setup, find_packages
import os


release_info = {}
infopath = os.path.join(os.path.dirname(__file__), "pydcmio", "info.py")
with open(infopath) as open_file:
    exec(open_file.read(), release_info)
pkgdata = {
    "pydcmio": ["tests/*.py", "tests/*/*.py"],
    "pydcmio": ["dcmconverter/dcm2nii_config.json"],
    "pydcmio": ["dcmanonymizer/*.json"]
}
scripts = [
    "pydcmio/scripts/pydcmio_dicom2nifti",
    "pydcmio/scripts/pydcmio_dicomanonymizer",
    "pydcmio/scripts/pydcmio_dicomreader",
    "pydcmio/scripts/pydcmio_splitseries",
    "pydcmio/scripts/pydcmio_transcode"
]


# Build the setup
setup(
    name=release_info["NAME"],
    description=release_info["DESCRIPTION"],
    long_description=release_info["LONG_DESCRIPTION"],
    license=release_info["LICENSE"],
    classifiers=release_info["CLASSIFIERS"],
    author=release_info["AUTHOR"],
    author_email=release_info["AUTHOR_EMAIL"],
    version=release_info["VERSION"],
    url=release_info["URL"],
    packages=find_packages(exclude="doc"),
    platforms=release_info["PLATFORMS"],
    extras_require=release_info["EXTRA_REQUIRES"],
    install_requires=release_info["REQUIRES"],
    package_data=pkgdata,
    scripts=scripts
)
