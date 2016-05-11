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
import json
import random
import dicom

# Bredala import
try:
    import bredala
    bredala.USE_PROFILER = False
    bredala.register("pydcmio.dcmconverter.dicom_utils",
                     names=["generate_config", "dcm2nii", "add_meta_to_nii",
                            "mosaic"])
except:
    pass

# Dcmio import
from pydcmio.dcmconverter.dicom_utils import generate_config
from pydcmio.dcmconverter.dicom_utils import dcm2nii
from pydcmio.dcmconverter.dicom_utils import add_meta_to_nii
from pydcmio.dcmconverter.dicom_utils import mosaic
from pydcmio.dcmreader.dcmreader import walk


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

python $HOME/git/pydcmio/pydcmio/scripts/dicom2nifti.py \
    -v 2 \
    -d /volatile/nsap/dcm2nii/dicom/T2GRE \
    -o /volatile/nsap/dcm2nii/convert/T2GRE \
    -t
    -r /path/to/input/transcoding/table
    -s /path/to/output/transcoding/table
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
    "-e", "--erase", dest="erase", action="store_true",
    help="if activated, clean the conversion output folder.")
parser.add_argument(
    "-d", "--dcmdir", dest="dcmdir", required=True, metavar="PATH",
    help="the folder that contains the DICOMs to be converted.",
    type=is_directory)
parser.add_argument(
    "-o", "--outdir", dest="outdir", required=True, metavar="PATH",
    help="the folder that contains the generated Nifti files.",
    type=is_directory)
parser.add_argument(
    "-t", "--transcode", dest="transcode", required=False, action="store_true",
    help="if activated, the subject ID is transcoded")
parser.add_argument(
    "-r", "--table", dest="in_table", required=False, default=None,
    help="The transcoding table, if not provided, new IDs are generated")
parser.add_argument(
    "-s", "--outtable", dest="out_table", required=False, default=None,
    help="The transcoding table to create/complete with processed subjects")
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

# get original ID
dcm_file = os.listdir(args.dcmdir)[0]
ds = dicom.read_file(os.path.join(args.dcmdir, dcm_file))
old_id = walk(ds, (0x0010, 0x0010), stack_values=False)

if old_id is None:
    niidir = os.path.join(args.outdir, "unknown")

# don't transcode unknown ID
elif args.transcode:
    if args.in_table and os.path.isfile(args.in_table):
        try:
            with open(args.in_table, 'r') as _file:
                in_tt = json.load(_file)
        except:
            raise ValueError("ERROR: the input transcoding table has an "
                             "incorrect format")
    else:
        in_tt = {}

    if args.out_table and os.path.isfile(args.out_table):
        try:
            with open(args.out_table, 'r') as _file:
                out_tt = json.load(_file)
            known_ids = []
            for subject, new_id in out_tt.items():
                known_ids.append(new_id)
        except:
            raise ValueError("ERROR: the output transcoding table has an "
                             "incorrect format")
    else:
        known_ids = []
        out_tt = {}

    # if original id in input transcoding table, use existing transcodage
    if old_id in in_tt:
        new_id = in_tt[old_id]
    # generate new transcodage
    else:
        # generate new id
        new_id = random.randint(100000000000, 999999999999)
        while new_id in known_ids:
            new_id = random.randint(100000000000, 999999999999)

        new_id = str(new_id)

        out_tt.update({old_id: new_id})

    niidir = os.path.join(args.outdir, new_id)

else:
    niidir = os.path.join(args.outdir, old_id)

# create output directory
if os.path.isdir(niidir):
    if args.erase:
        shutil.rmtree(niidir)
    else:
        raise ValueError("ERROR: The output directory '{}' already "
                         "exists".format(niidir))

os.makedirs(niidir)

# generate out transcoding table if transcoding allowed

if args.transcode:
    # CAN BE DANGEROUS IN CASE OF PARALLEL RUNING, I'm putting this here
    # so it does not have to wait for dcm conversion before writing in the
    # table
    # if table modified between it's parsing above and here... it will be lost
    if args.out_table:
        out_table_file = args.out_table
    else:
        out_table_file = os.path.join(niidir, "transcoding_table.json")
    if args.verbose > 0:
        print("[log] update output transcoding table")
    with open(out_table_file, 'w') as _file:
        json.dump(out_tt, _file, indent=2)


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
tags = [("TR", [("0x0018", "0x0080")]),
        ("TE", [("0x0018", "0x0081")])]
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
