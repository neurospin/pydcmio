##########################################################################
# NSAp - Copyright (C) CEA, 2017
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

"""
Defacing with the Poldrack, R. 'pydeface' Python module.
"""

# System import
import os
import warnings

# Pyconnectome
try:
    from pyconnectome import DEFAULT_FSL_PATH
    from pyconnectome.wrapper import FSLWrapper
except:
    DEFAULT_FSL_PATH = ""
    warnings.warn("PyConnectome is not installed.")


def deface(input_files, outdir, reference_file=None, fsl_sh=DEFAULT_FSL_PATH):
    """ Deface MRI head images using Poldrack, R. 'pydeface' Python module.

    Parameters
    ----------
    input_files: list of str
        Input MRI head images to be defaced.
    outdir: str
        The output folder.
    reference_file: str (optional, default None)
        The image that must be used as reference if more than one image
        have been supplied as input.
    fsl_sh: str (optional, default DEFAULT_FSL_PATH)
        The FSL configuration file.

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

    # Link the input files
    local_input_files = []
    for fp in input_files:
        local_input_files.append(os.path.join(outdir, os.path.basename(fp)))
        if not os.path.exists(local_input_files[-1]):
            os.symlink(fp, local_input_files[-1])
        else:
            warnings.warn(
                "'{0}' file already here.".format(local_input_files[-1]))

    # Define the command
    deface_file = os.path.join(
        outdir, "pydeface_" + os.path.basename(input_files[0]))
    cmd = ["pydeface.py", local_input_files[0], deface_file]

    # Call defacing
    wrapper = FSLWrapper(cmd, shfile=fsl_sh, env=os.environ)
    wrapper()

    # Remove links
    for fp in local_input_files:
        os.remove(fp)

    return [deface_file], None
