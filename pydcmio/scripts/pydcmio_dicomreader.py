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
import json
import inspect
import ast

# Bredala import
try:
    import bredala
    bredala.USE_PROFILER = False
    bredala.register("pydcmio.dcmreader.dcmreader",
                     names=["walk", "walker_callback"])
except:
    pass

# Dcmio import
from dcmio.dcmreader import dcmreader

# Parameters to keep trace
__hopla__ = ["dcmdir", "niidir", "config_file", "files, reoriented_files",
             "reoriented_and_cropped_files", "bvecs", "bvals",
             "filled_nii_files", "figures"]


# Script documentation
doc = """
Dicom reader and value extractor
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This code enables us to extract any kind of information from a dicom file.

Dicom field sequences are parsed recursively (deep search) to handle
enhanced storage parsing.

Steps:

1- chose which mode you want to use:
    free (you provide the dicom tags)
    guided (tags are automatically provided)
2- The extraction is performed and the values are returned and written in
    a json file

Command:

python $HOME/git/pydcmio/pydcmio/scripts/pydcmio_dicomreader.py \
    -v 2 \
    -t '(0x0018, 0x1312)' \
    -f path/to/dcm \
    -o path/to/json \
    -s \
    -e

or

python $HOME/git/pydcmio/pydcmio/scripts/pydcmio_dicomreader.py \
    -v 2 \
    -a get_b_vectors \
    -f path/to/dcm \
    -o path/to/json
"""


def is_file(filearg):
    """ Type for argparse - checks that output file exists.
    """
    if not os.path.isfile(filearg):
        raise argparse.ArgumentError(
            "The file '{0}' does not exist!".format(filearg))
    return filearg

function_names = []
functions = []
for _func in inspect.getmembers(dcmreader, inspect.isfunction):
    if _func[0] not in ["walk", "walker_callback"]:
        function_names.append(_func[0])
        functions.append(_func[1])

parser = argparse.ArgumentParser(description=doc)
parser.add_argument(
    "-v", "--verbose", dest="verbose", type=int, choices=[0, 1, 2], default=0,
    help="increase the verbosity level: 0 silent, [1, 2] verbose.")
parser.add_argument(
    "-e", "--erase", dest="erase", action="store_true",
    help="if activated, clean the json output file.")
group = parser.add_mutually_exclusive_group()
group.add_argument(
    "-t", "--tag", dest="dcmtag",
    help=("the tags you wich to extract from the dicom file, string such as "
          "type(repr(<tag>)) == tuple."),
    type=str)
group.add_argument(
    "-a", "--func", dest="func",
    help="use an already provided function: {}".format(function_names))
parser.add_argument(
    "-o", "--outfile", dest="outfile", required=True, metavar="PATH",
    help="the file that contains the extracted values.")
parser.add_argument(
    "-f", "--dcmfile", dest="dcmfile", required=True, metavar="PATH",
    help="the dicom file to parse",
    type=is_file)
parser.add_argument(
    "-s", "--stack", dest="stack", action="store_true",
    help=("if specified, the output file will contain all values that "
          "correspond to a given tag, not only the first one."))
args = parser.parse_args()


"""
Check if the output file exists on the file system, and clean it if requested.
"""
if args.verbose > 0:
    print("[info] Start dicom tag extraction...")
    print("[info] Dicom file: {0}.".format(args.dcmfile))
    print("[info] Output: {0}.".format(args.outfile))

if os.path.isfile(args.outfile) and not args.erase:
    raise ValueError("ERROR: The output file '{}' already exists".format(
        args.outfile))
else:
    if not os.path.isdir(os.path.dirname(args.outfile)):
        os.makedirs(os.path.dirname(args.outfile))

if args.dcmtag:
    _tag = ast.literal_eval(args.dcmtag)
    if type(_tag) != tuple:
        raise TypeError("ERROR: the value provided as dicom tag '{}'is not a "
                        "tuple".format(args.dcmtag))


class UnknownFunction(Exception):

    def __init__(self, expr, msg):
        self.expr = expr
        self.msg = msg

    def __str__(self):
        return repr(self.msg)


"""
dicom field extraction
"""
out = {}
if args.func:
    if not args.func in function_names:
        raise UnknownFunction(args.func,
                              "function '{}' is not implemented yet".format(
                                  args.func))
    else:
        _func = functions[function_names.index(args.func)]
        result = _func(args.dcmfile, args.stack)
    out["function"] = args.func


else:
    import dicom
    ds = dicom.read_file(args.dcmfile)
    result = dcmreader.walk(dataset=ds, _tag=_tag, stack_values=args.stack)
    out["tags"] = args.dcmtag

out["dicom_file"] = args.dcmfile
out["stack"] = args.stack
out["values"] = result

"""
Print results in output file
"""

with open(args.outfile, 'w') as _file:
    json.dump(out, _file, indent=3)


if args.verbose > 1:
    print("[result] Files: {0}.".format(args.outfile))
