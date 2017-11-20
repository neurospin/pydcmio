##########################################################################
# NSAp - Copyright (C) CEA, 2017
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

"""
Module that provides usefull functions to deface an image.
"""

from .mask_face import deface as mask_face
from .mri_deface import deface as mri_deface
from .pdeface import deface as pdeface
