#! /usr/bin/env python
##########################################################################
# NSAp - Copyright (C) CEA, 2013-2016
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
from __future__ import print_function
import argparse
import os
import shutil
import numpy

# Bredala import
try:
    import bredala
    bredala.USE_PROFILER = False
    bredala.register("dcmio.dcmconverter.dicom_utils",
                     names=["generate_config", "dcm2nii", "add_meta_to_nii",
                            "mosaic"])
except:
    pass

# Dcmio import
from dcmio.dcmconverter.dicom_utils import generate_config
from dcmio.dcmconverter.dicom_utils import dcm2nii
from dcmio.dcmconverter.dicom_utils import add_meta_to_nii
from dcmio.dcmconverter.dicom_utils import mosaic


# Parameters to keep trace
__hopla__ = ["dcmdir", "niidir", "config_file", "files, reoriented_files",
             "reoriented_and_cropped_files", "bvecs", "bvals",
             "filled_nii_files", "figures"]


# Script documentation
doc = """
Dicom to Nifti conversion
~~~~~~~~~~~~~~~~~~~~~~~~~

Wraps around the 'dcm2nii' command.

This code enables us to convert DICOMs to Nifti using the Chris Rorden's
'dcm2nii' command.

The code is setup so that all the converted Nifti images are anonymized,
compressed in Nifti compressed '.nii.gz' format, and stacked in the same
image for 4D acquisitons. By default the proctocol is used to name the
generated files. On top of that some DICOM tags are stored in the
converted Nifti 'descrip' header field: the repetition
time TR and the echo time TE.

Steps:

1- create the 'dcm2nii' configuration file
2- 'dcm2nii' conversion
3- fill the nifti header
4- create a snap of the created volume(s)

Command:

python $HOME/git/caps-dcmio/dcmio/scripts/dicom2nifti.py \
    -v 2 \
    -d /volatile/nsap/dcm2nii/dicom/T2GRE \
    -o /volatile/nsap/dcm2nii/convert/T2GRE \
    -e
"""

def is_directory(dirarg):
    """ Type for argparse - checks that directory exists.
    """
    if not os.path.isdir(dirarg):
        raise argparse.ArgumentError(
            "The directory '{0}' does not exist!".format(dirarg))
    return dirarg


parser = argparse.ArgumentParser(description=doc)
parser.add_argument(
    "-v", "--verbose", dest="verbose", type=int, choices=[0, 1, 2], default=0,
    help="increase the verbosity level: 0 silent, [1, 2] verbose.")
parser.add_argument(
    "-e", "--errase", dest="errase", action="store_true",
    help="if activated, clean the conversion output folder.")
parser.add_argument(
    "-d", "--dcmdir", dest="dcmdir", required=True, metavar="PATH",
    help="the folder that contains the DICOMs to be converted.",
    type=is_directory)
parser.add_argument(
    "-o", "--outdir", dest="outdir", required=True, metavar="PATH",
    help="the folder that contains the generated Nifti files.",
    type=is_directory)
args = parser.parse_args()


"""
First check if the output directory exists on the file system, and
clean it if requested.
"""
if args.verbose > 0:
    print("[info] Start dicom conversion with dcm2nii...")
    print("[info] Directory: {0}.".format(args.dcmdir))
    print("[info] Output: {0}.".format(args.outdir))
dcmdir = args.dcmdir
niidir = args.outdir
if os.path.isdir(niidir) and args.errase:
    shutil.rmtree(niidir)
    os.mkdir(niidir)

"""
Create the 'dcm2nii' configuration file
"""
config_file = generate_config(
    niidir, anonymized=True, gzip=True, add_date=False,
    add_acquisition_number=False, add_protocol_name=True,
    add_patient_name=False, add_source_filename=False,
    begin_clip=0, end_clip=0)
if args.verbose > 1:
    print("[result] Configuration: {0}.".format(config_file))

"""
'dcm2nii' conversion
"""
files, reoriented_files, reoriented_and_cropped_files, bvecs, bvals = dcm2nii(
    dcmdir, o=niidir, b=config_file)
if args.verbose > 1:
    print("[result] Files: {0}.".format(files))
    print("[result] Reoriented files: {0}.".format(reoriented_files))
    print("[result] Reoriented and cropped files: {0}.".format(
        reoriented_and_cropped_files))
    print("[result] Bvecs: {0}.".format(bvecs))
    print("[result] Bvals: {0}.".format(bvals))

"""
Fill the nifti header
"""
tags = [("TR", ("0x0018", "0x0080")),
        ("TE", ("0x0018", "0x0081"))]
filled_nii_files = add_meta_to_nii(
    files, dcmdir, dcm_tags=tags, output_directory=niidir, prefix="filled")
if args.verbose > 1:
    print("[result] Filled files: {0}.".format(filled_nii_files))


"""
Create a snap of the created volume(s)
"""
figures = []
for impath in filled_nii_files:
    if len(bvals) == 0:
        snap = mosaic(impath, niidir, strategy="average")
        figures.append(snap)
    else:
        indices = numpy.where(numpy.loadtxt(bvals[0]) != 0)[0].tolist()
        snap = mosaic(impath, niidir, strategy="pick", indices=indices,
                      title="dwi")
        figures.append(snap)
        indices = numpy.where(numpy.loadtxt(bvals[0]) == 0)[0].tolist()
        snap = mosaic(impath, niidir, strategy="pick", indices=indices,
                      title="b0")
        figures.append(snap)
if args.verbose > 1:
    print("[result] Snaps: {0}.".format(figures))

