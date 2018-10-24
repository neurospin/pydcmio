##########################################################################
# NSAp - Copyright (C) CEA, 2017
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

"""
Defacing with the Marcus, D. 'mask_face' command.
"""

# System import
import os
import shutil
import nibabel
import warnings

# Pyconnectome
try:
    from pyconnectome import DEFAULT_FSL_PATH
    from pyconnectome.wrapper import FSLWrapper
except:
    DEFAULT_FSL_PATH = ""
    warnings.warn("PyConnectome is not installed.")


def deface(input_files, outdir, matlab_mcr, reference_file=None,
           mask_ears=True, verbose=0, rm_workspace=False,
           fsl_sh=DEFAULT_FSL_PATH):
    """ Deface MRI head images using the Marcus, D. 'mask_face' command.

    This code is standalone and does not need matlab licence. You just need
    MathWorks MCR software installed on your computer.

    Parameters
    ----------
    input_files: list of str
        Input MRI head images to be defaced.
    outdir: str
        The output folder.
    matlab_mcr:str
        The MATLAB MCR directory for standalone applications.
    reference_file: str (optional, default None)
        The image that must be used as reference if more than one image
        have been supplied as input.
    mask_ears: bool (optional, default True)
        If activated, masks ears.
    verbose: int (optional, default 0)
        The verbosity level.
    rm_workspace: bool (optional, default False)
        If activated, keep the defacing workspace (require more disk space).
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
        if reference_file is None or reference_file not in input_files:
            raise ValueError("If more than one image is specified, you must "
                             "also specify one of them as reference. The "
                             "reference image will be used for spatial "
                             "co-registration with an atlas, and others will "
                             "use the reference facial mask.")

    # Convert in analyse format
    pair_files = []
    basenames = []
    affines = []
    for fp in input_files:
        fp = os.path.abspath(fp)
        basenames.append(os.path.basename(fp).split(".")[0])
        pair_filepath = os.path.join(outdir, "{0}.img".format(basenames[-1]))
        im = nibabel.load(fp)
        affines.append(im.affine)
        pair_im = nibabel.Nifti1Pair(im.get_data(), im.affine)
        pair_im.to_filename(pair_filepath)
        pair_files.append(pair_filepath)

    # Define the command
    cmd = ["mask_face", ",".join([fp[:-len(".img")] for fp in pair_files])]
    cmd += ["-a"]
    cmd += ["-v", "{0}".format(verbose)]
    if reference_file is not None:
        ref_index = input_files.index(reference_file)
        cmd += ["-r", pair_files[ref_index]]
    if mask_ears:
        cmd += ["-e", "1"]

    # Call defacing
    deface_env = os.environ
    deface_env["MASKFACE_MCR"] = matlab_mcr
    wrapper = FSLWrapper(
        cmd, shfile=fsl_sh, env=deface_env)
    wrapper(cwdir=outdir)

    # Deal with outputs: nifti + move
    deface_files = []
    snap_files = []
    wdir = os.path.join(outdir, "maskface")
    for fp, basename, aff in zip(pair_files, basenames, affines):
        deface_pair_file = os.path.join(
            wdir, "{0}_full_normfilter.hdr".format(basename))
        nii_file = os.path.join(
            outdir, "{0}_full_normfilter.nii.gz".format(basename))
        im = nibabel.load(deface_pair_file)
        nii_im = nibabel.Nifti1Image(im.get_data(), aff)
        nibabel.save(nii_im, nii_file)
        del im, nii_im
        deface_files.append(nii_file)
        snap_files.append(
            os.path.join(outdir, "{0}_normfilter.png".format(basename)))
        shutil.copy2(
            os.path.join(wdir, "{0}_normfilter.png".format(basename)),
            snap_files[-1])
        os.remove(fp)
        os.remove(fp.replace(".img", ".hdr"))
    if rm_workspace:
        shutil.rmtree(wdir)
    else:
        shutil.move(wdir, os.path.join(outdir, "workspace"))

    return deface_files, snap_files
