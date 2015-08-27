#! /usr/bin/env python
##########################################################################
# NSAp - Copyright (C) CEA, 2015
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# Current version
version_major = 1
version_minor = 0
version_micro = 0

# Expected by setup.py: string of form "X.Y.Z"
__version__ = "{0}.{1}.{2}".format(version_major, version_minor, version_micro)

# Expected by setup.py: the status of the project
CLASSIFIERS = ["Development Status :: 5 - Production/Stable",
               "Environment :: Console",
               "Environment :: X11 Applications :: Qt",
               "Operating System :: OS Independent",
               "Programming Language :: Python",
               "Topic :: Scientific/Engineering",
               "Topic :: Utilities"]

# Project descriptions
description = "CAPS-DCMIO"
long_description = """
==========
CAPS-DCMIO
==========

[dcmio] DiCoM IO.
A pure python tool that defines processing pipelines to convert and
anonymize dicoms. The pipeline are described in XML and interpreted by
a pipeline engine.
"""

# Dependencies
SPHINX_MIN_VERSION = 1.0
DICOM_MIN_VERSION = 0.9
CAPSUL_VERSION = 1.0
MMUTILS_VERSION = 1.0

# Main setup parameters
NAME = "dcmio"
ORGANISATION = "CEA"
MAINTAINER = "Antoine Grigis"
MAINTAINER_EMAIL = "antoine.grigis@cea.fr"
DESCRIPTION = description
LONG_DESCRIPTION = long_description
URL = "https://github.com/neurospin/caps-dcmio.git"
DOWNLOAD_URL = "https://pypi.python.org/pypi/caps-dcmio/" + __version__
LICENSE = "CeCILL-B"
CLASSIFIERS = CLASSIFIERS
AUTHOR = "CAPS-DCMIO developers"
AUTHOR_EMAIL = "antoine.grigis@cea.fr"
PLATFORMS = "OS Independent"
ISRELEASE = True
VERSION = __version__
PROVIDES = ["dcmio"]
REQUIRES = [
    "capsul=={0}".format(CAPSUL_VERSION),
    "mmutils=={0}".format(MMUTILS_VERSION),
    "pydicom>={0}".format(DICOM_MIN_VERSION)
]
EXTRA_REQUIRES = {
    "doc": [
        "sphinx>=1.0",
    ]
}
