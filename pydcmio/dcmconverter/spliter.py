##########################################################################
# NSAp - Copyright (C) CEA, 2013 - 2016
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

"""
Module that provides tools to reorganize DICOM files.
"""


# System import
from __future__ import print_function
import os
import sys
import shutil
import string
import traceback

# Third party import
import progressbar
import dicom


def decode(attribute):
    """Decode DICOM attributes from ISO_IR 100.

    DICOM headers are routinely encoded with ISO_IR 100 which is
    equivalent to IS0 8859-1.

    We currently expect all our DICOM headers to be encoded using
    ISO_IR 100. In this context DICOM string attributes returned
    by pydicom are 8-bit strings encoded with ISO_IR 100.

    Parameters
    ----------
    attribute  : str
        The 8-bit string to decode from ISO_IR 100.

    Returns
    -------
    unicode
        The decoded string.

    """
    return attribute.decode("latin_1")


_ILLEGAL_CHARACTERS = u"\\/:*?'<>|_ \t\r\n\0[],;"
_CLEANUP_TABLE = dict((ord(char), u"-") for char in _ILLEGAL_CHARACTERS)


def cleanup(attribute):
    """Get rid of illegal characters in DICOM attributes.

    Replace characters that are illegal in pathnames.
    - Windows reserved characters
    - '_' since it is reserved by Brainvisa
    - spaces, tab, newline and null character

    Parameters
    ----------
    attribute  : unicode
        Decoded string.

    Returns
    -------
    unicode
        String with illegal characters replaced.

    """
    return attribute.translate(_CLEANUP_TABLE)


def split_series(dicom_dir, outdir, skip_non_dicom_files=False,
                 check_session=True, check_encoding=True):
    """ Split all the folder Dicom files by series in different folders.

    Dicom files are searched recursively in the input folder and all files
    are expected to be Dicom files.

    Expect to split files from a single session.

    Parameters
    ----------
    dicom_dir: str (mandatory)
        a folder containing Dicom files to organize by series.
    outdir: str (mandatory)
        the destination folder.
    skip_non_dicom_files: bool (optional, default False)
        if True skip non DICOM files, otherwise raise an error.
    check_session: bool (optional, default True)
        if True check if the DICOM files are in the same session and split
        files by sequences (raise an error if it is not the case), otherwise
        simply rename the DICOM files using the SOP instance UID.
    check_encoding: bool (optional, default True)
        if True check if the DICOM files encoding (expect ISO_IR 100). If the
        file is not encoded properly, the file is not considered.
    """
    # Read the incoming directory:
    # process each file in this directory and its sub-directories
    # expect each file to be a DICOM file
    to_treat_dicom = []
    for root, dirs, files in os.walk(dicom_dir):
        to_treat_dicom.extend([
            os.path.join(root, basename) for basename in files])

    # Go through each file: expected to be in Dicom format
    acquisition_datetime = None
    with progressbar.ProgressBar(max_value=len(to_treat_dicom),
                                 redirect_stdout=True) as bar:
        for cnt, dicom_file in enumerate(to_treat_dicom):
            _split(dicom_file, acquisition_datetime, outdir,
                   skip_non_dicom_files, check_session, check_encoding)
            bar.update(cnt)


def safe_run(func):
    """ Decorator that print the function args and kwargs before raising an
    exception.
    """
    def func_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print("-" * 50)
            print(args)
            print(kwargs)
            print("-" * 50)
            raise e
    return func_wrapper


@safe_run
def _split(dicom_file, acquisition_datetime, outdir, skip_non_dicom_files,
           check_session, check_encoding):
    """ Split function, see 'split_series' for more information.
    """
    # Get the time of last modification
    mtime = os.path.getmtime(dicom_file)

    # Read DICOM dataset
    try:
        dataset = dicom.read_file(dicom_file)
    except:
        if skip_non_dicom_files:
            return
        traceback.print_exc(file=sys.stdout)
        raise ValueError(
            "'{0}' is not a valid DICOM file.".format(dicom_file))

    # Find character encoding of DICOM attributes:
    # we currently expect encoding to be ISO_IR 100
    if check_encoding:
        if (0x0008, 0x0005) in dataset:
            SpecificCharacterSet = dataset[0x0008, 0x0005].value
            if SpecificCharacterSet != "ISO_IR 100":
                print("'{0}' file encoding is not ISO_IR 100 as "
                      "expected.".format(dicom_file))
                return
        else:
            print("Can't check encoding of '{0}', missing "
                  "(0x0008, 0x0005) tag.".format(dicom_file))

    # Process other DICOM attributes:
    # decode strings assuming 'ISO_IR 100'
    SeriesDescription = None
    if (0x0008, 0x0018) not in dataset:
        if skip_non_dicom_files:
            return
        raise ValueError(
            "'{0}' does not contain a SOPInstanceUID.".format(
                dicom_file))
    SOPInstanceUID = dataset[0x0008, 0x0018].value
    if (0x0008, 0x103e) in dataset:
        SeriesDescription = cleanup(
            decode(dataset[0x0008, 0x103e].value))
    if check_session:
        SeriesNumber = dataset[0x0020, 0x0011].value
        if (0x0018, 0x0081) in dataset:
            EchoTime = dataset[0x0018, 0x0081].value
        else:
            EchoTime = "NA"

    # Check the session time
    if check_session:
        current_acquisition_datetime = (dataset[0x0008, 0x0020].value +
                                        dataset[0x0008, 0x0030].value)
        if acquisition_datetime is None:
            acquisition_datetime = current_acquisition_datetime
        elif acquisition_datetime != current_acquisition_datetime:
            print(
                "Two sessions detected in the input folder '{0}': {1} "
                "- {2}.".format(dicom_dir, acquisition_datetime,
                                current_acquisition_datetime))
            if SeriesDescription:
                SeriesDescription += "_{0}".format(
                    current_acquisition_datetime)
            else:
                SeriesDescription = current_acquisition_datetime

    # Build the full path to the outgoing directory:
    # we assume that there is only one session
    if check_session:
        if SeriesDescription:
            serie_name = (SeriesDescription + "_" + str(EchoTime) +
                          "_" + str(SeriesNumber).rjust(6, "0"))
        else:
            serie_name = (str(EchoTime) + "_" +
                          str(SeriesNumber).rjust(6, "0"))
    else:
        serie_name = "all_dicoms"
    output_dicom_dir = os.path.join(outdir, serie_name)

    # Check that the destination folder exists
    if not os.path.isdir(output_dicom_dir):
        os.mkdir(output_dicom_dir)

    # Build a new name for the DICOM file
    output_dicom_file = os.path.join(output_dicom_dir,
                                     SOPInstanceUID + '.dcm')

    # Copy DICOM file:
    # handle case where outgoing file already exists
    if os.path.exists(output_dicom_file):

        # Compare modification time and keep the most recent file
        if os.path.getmtime(output_dicom_file) < mtime:
            shutil.copy2(dicom_file, output_dicom_file)

    # file does not exists and can be copied
    else:
        shutil.copy2(dicom_file, output_dicom_file)
