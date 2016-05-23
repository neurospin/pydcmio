##########################################################################
# NSAp - Copyright (C) CEA, 2013 - 2016
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
import os
import sys
import shutil
import string
import dicom
from pip.utils.ui import DownloadProgressBar


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


_ILLEGAL_CHARACTERS = u"\\/:*?'<>|_ \t\r\n\0"
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


def split_series(dicom_dir, outdir):
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
    """
    # Read the incoming directory:
    # process each file in this directory and its sub-directories
    # expect each file to be a DICOM file
    to_treat_dicom = []
    for root, dirs, files in os.walk(dicom_dir):
        to_treat_dicom.extend([
            os.path.join(root, basename) for basename in files])

    # Go through each file: expected to be in Dicom format
    progress_indicator = DownloadProgressBar(max=len(to_treat_dicom))
    acquisition_datetime = None
    for dicom_file in to_treat_dicom:

        # Update progress bar
        statinfo = os.stat(dicom_file)
        DownloadProgressBar.suffix = "{0:.3f}MB".format(
            statinfo.st_size / 10e5)
        progress_indicator.next(1)

        # Get the time of last modification
        mtime = os.path.getmtime(dicom_file)

        # Read DICOM dataset
        dataset = dicom.read_file(dicom_file)

        # Find character encoding of DICOM attributes:
        # we currently expect encoding to be ISO_IR 100
        if (0x0008, 0x0005) in dataset:
            SpecificCharacterSet = dataset[0x0008, 0x0005].value
            if SpecificCharacterSet != "ISO_IR 100":
                print("'{0}' file encoding is not ISO_IR 100 as "
                      "expected.".format(dicom_file))
                continue
        else:
            print("Can't check encoding of '{0}', missing (0x0008, 0x0005) "
                  "tag.".format(dicom_file))

        # Process other DICOM attributes:
        # decode strings assuming 'ISO_IR 100'
        SeriesDescription = None
        SOPInstanceUID = dataset[0x0008, 0x0018].value
        if (0x0008, 0x103e) in dataset:
            SeriesDescription = cleanup(decode(dataset[0x0008, 0x103e].value))
        SeriesNumber = dataset[0x0020, 0x0011].value
        EchoTime = dataset[0x0018, 0x0081].value

        # Check the session time
        current_acquisition_datetime = (dataset[0x0008, 0x0020].value +
                                        dataset[0x0008, 0x0030].value)
        if acquisition_datetime is None:
            acquisition_datetime = current_acquisition_datetime
        elif acquisition_datetime != current_acquisition_datetime:
            raise ValueError(
                "Two sessions detected in the input folder '{0}': {1} - "
                "{2}.".format(dicom_dir, acquisition_datetime,
                              current_acquisition_datetime))

        # Build the full path to the outgoing directory:
        # we assume that there is only one session
        if SeriesDescription:
            serie_name = (SeriesDescription + "_" + str(EchoTime) + "_" +
                          str(SeriesNumber).rjust(6, "0"))
        else:
            serie_name = str(EchoTime) + "_" + str(SeriesNumber).rjust(6, "0")
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
