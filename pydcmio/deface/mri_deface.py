##########################################################################
# NSAp - Copyright (C) CEA, 2017
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

"""
Defacing with the FreeSurfer 'mri_deface' command.
"""

# System import
import os
import warnings

# Pyfreesurfer import
try:
    from pyfreesurfer.wrapper import FSWrapper
    from pyfreesurfer import DEFAULT_FREESURFER_PATH
except:
    DEFAULT_FREESURFER_PATH = ""
    warnings.warn("PyFreeSurfer is not installed.")


def deface(input_files, outdir, reference_file=None,
           verbose=0, fs_config=DEFAULT_FREESURFER_PATH):
    """ Deface MRI head images using the FreeSurfer 'mri_deface' command.


    Parameters
    ----------
    input_files: list of str
        Input MRI head images to be defaced.
    outdir: str
        The output folder.
    reference_file: str (optional, default None)
        The image that must be used as reference if more than one image
        have been supplied as input.
    verbose: int (optional, default 0)
        The verbosity level.
    fs_config: str (optional, default DEFAULT_FREESURFER_PATH)
        The FreeSurfer configuration file.

    Returns
    -------
    deface_files: list of str
        The defaced input MRI head images.
    snap_files: list of str
        The corresponding snaps that can be used to check the defacing result.
    """
    # Check input parameters
    outdir = os.path.abspath(outdir)
    if len(input_files) == 0:
        raise ValueError("You must specify at least one image.")
    elif len(input_files) > 1:
        raise ValueError("Mutliple input files not yet supported.")
        # if reference_file is None or reference_file not in input_files:
        #     raise ValueError("If more than one image is specified, you must "
        #                      "also specify one of them as reference. The "
        #                      "reference image will be used for spatial "
        #                      "co-registration with an atlas, and others "
        #                      "will use the reference facial mask.")

    # Define the command
    deface_file = os.path.join(outdir, os.path.basename(input_files[0]))
    wrapper = FSWrapper([], shfile=fs_config)
    face_file = os.path.join(
        wrapper.environment["FREESURFER_HOME"], "average", "face.gca")
    skull_file = os.path.join(
        wrapper.environment["FREESURFER_HOME"], "average",
        "talairach_mixed_with_skull.gca")
    cmd = ["mri_deface", input_files[0], skull_file, face_file, deface_file]

    # Call defacing
    wrapper = FSWrapper(cmd, shfile=fs_config)
    wrapper()

    return [deface_file], None
