##########################################################################
# NSAP - Copyright (C) CEA, 2015
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
import os
import json
import re
import dicom
from pip.utils.ui import DownloadProgressBar

# Dcmio import
from .callbacks import callback_private
from .callbacks import callback_xxxx
from .callbacks import ANON_LOG
from .callbacks import MANUFACTURER
from .callbacks import PRIVATE_DEIDENTIFY
from .callbacks import CALLBACKS
from .callbacks import TAGS
from .utils import add_dataelement
from .utils import replace_by
from .utils import repr_dataelement


def anonymize_dicomdir(inputdir, outdir, write_logs=True):
    """ Anonymize all DICOM files of the input directory.

    Parameters
    ----------
    inputdir: str (mandatory)
        A folder that contains only DICOM files to be anonymized.
    outdir: str (mandatory)
        The anonimized DICOM files folder.
    write_logs: bool (optional, default True)
        If True write the anonimization logs.

    Returns
    -------
    dcmfiles: str
        The anonimized DICOM files.
    logfiles: list
        The anonimization log files.

    """
    # Load the first dataset
    input_dicoms = [os.path.join(inputdir, fname)
                    for fname in os.listdir(inputdir)]
    dataset = dicom.read_file(input_dicoms[0], force=True)

    # Load the tags to anonymize
    filedir = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(filedir, "deidentify.json"), "r") as open_file:
        anon_tags = json.load(open_file)[1:]

    # Set up the desired callbacks and tags to be anonymized
    # Iterate over all the tag to anonymize according to PS 3.15-2008 and
    # supplement 142
    for tag_item in anon_tags:
        tag_repr = tag_item["Tag"][1:-1]
        action = tag_item["Basic Profile"]
        group, element = tag_repr.split(",", 1)

        # Deal with special tags
        if "xx" in group or "xx" in element:
            pattern = re.compile(tag_repr.replace("x", "[0-9A-Fa-f]"))
            CALLBACKS[tag_repr] = [pattern, callback_xxxx]

        # Deal with private tags
        elif "gggg" in group:
            if (0x0008, 0x0070) in dataset:
                MANUFACTURER.append(dataset[0x0008, 0x0070].value)
            if len(MANUFACTURER) > 0:
                CALLBACKS[tag_repr] = [None, callback_private]
            else:
                raise Exception(
                    "The '(0008,0070)' manufacturer tag is not specified and "
                    "is required to anonymize private tags.")

        # Deal with standard tags
        else:
            TAGS[tag_repr] = (int(group, 16), int(element, 16)), action

    # Now compile the diffusion private tags patterns
    filedir = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(filedir, "private_deidentify.json"),
              "r") as open_file:
        private_anons = json.load(open_file)
    for key, values in private_anons.items():
        for value in values:
            pattern = re.compile(value["Tag"].replace("x", "[0-9A-Fa-f]"))
            PRIVATE_DEIDENTIFY.setdefault(key, []).append(pattern)

    # Process all DICOM files
    progress_indicator = DownloadProgressBar(max=len(input_dicoms))
    dcmfiles = []
    logfiles = []
    for cnt, input_dicom in enumerate(input_dicoms):
        statinfo = os.stat(input_dicom)
        DownloadProgressBar.suffix = "{0:.3f}MB".format(
            statinfo.st_size / 10e5)
        progress_indicator.next(1)
        output_dicom, output_log = anonymize_dicomfile(
            input_dicom, outdir, outname=str(cnt), write_log=write_logs)
        dcmfiles.append(output_dicom)
        logfiles.append(output_log)
    progress_indicator.finish()

    return dcmfiles, logfiles


def anonymize_dicomfile(input_dicom, outdir, outname=None, write_log=True):
    """ Anonymize DICOMs

    According to PS 3.15-2008, basic application level de-indentification of
    a DICOM file requires replacing the values of a set of data elements and
    the supplement 142 on the clinical trial de-identification profiles. All
    the anonymized fields are replaced and may be set in future into the
    encrypted attributes sequence (0400,0550). In the standard it is not
    required that the Encrypted Attributes Dataset be created; indeed, there
    may be circumstances where the Dataset is expected to be archived long
    enough that any contemporary encryption technology may be inadequate
    to provide long term protection against unauthorized recovery of
    identification.

    The applied de-identification methods are:

    * 113100 - Basic Application Confidentiality Profil
    * 113103 - Clean Graphics Option
    * 113109 - Retain Device Identity Option

    To do:

    * 113102 - Clean Recognizable Visual Features Option

    What does this function:

    * All fields specified in the 'anon_tags' structure are replaced with
      the 'anon_value'.
    * To remove all private tags a group 'gggg' has to be specified in the
      'anon_tags' structure.
    * A log is save with all the anonymization operations.

    Parameters
    ----------
    input_dicom: str (mandatory)
        a dicom file path to be processed.
    outdir: str (mandatory)
        the directory where the anonymized DICOM file and a Json file
        containing a dictionary of the modified tags are generated.
    outname: str (optional, default None)
        the generated files base names, if None use the 'input_dicom' base
        name.
    write_log: bool (optional, default True)
        If True write the anonimization log.

    Returns
    -------
    output_dicom: str
        the path to the anonimized DICOM file.
    output_log: str
        If 'write_log' is set, the path to the anonimization log.
    """
    # Clean global log
    for key in ANON_LOG.keys():
        ANON_LOG.pop(key)

    # Load the DICOM dataset to anonymize
    if outname is None:
        basedicom = os.path.basename(input_dicom)
        outname = basedicom.split(".")[0]
    else:
        basedicom = outname + ".dcm"
    dataset = dicom.read_file(input_dicom, force=True)

    # Anonymize the dataset
    anonymize_dataset(dataset)

    # Save the anonymized DICOM
    output_dicom = os.path.join(outdir, basedicom)
    dataset.save_as(output_dicom)

    # Save the anonimized log
    output_log = None
    if write_log:
        output_log = os.path.join(outdir, outname + ".json")
        with open(output_log, "w") as open_file:
            json.dump(ANON_LOG, open_file, indent=4)

    return output_dicom, output_log


def anonymize_dataset(dataset, level=1):
    """ Anonymize a pydicom dataset.

    Parameters
    ----------
    dataset: dicom.dataset.Dataset (mandatory)
        a dataset to anonymize.
    """
    # Anonymize the registered tags
    for tag, action in TAGS.values():
        if tag in dataset:
            data_element = dataset[tag]
            tag_repr = repr(data_element.tag)[1:-1].replace(" ", "")
            value = data_element.value
            anon_value = replace_by(value, data_element.VR, action)
            value_repr = repr_dataelement(data_element)
            ANON_LOG.setdefault(tag_repr, []).append((value_repr, anon_value))
            if anon_value is None:
                dataset.pop(data_element.tag)
            else:
                data_element.value = anon_value

    # Anonymize the current dataset applying the registered callbacks
    dataset.walk(callback_main)

    # In supplement 142 the attribute Patient Identity Removed shall be
    # replaced or added to the dataset and the method used for identification
    # need to be specified
    if level == 1:
        add_dataelement(dataset, (0x0012, 0x0062), "YES", "CS")
        add_dataelement(dataset, (0x0012, 0x0063), [
            "Basic Application Confidentiality Profil",
            "Clean Graphics Option",
            "Retain Device Identity Option"], "LO")
        sqdataset = []
        for value, desc in [
                ("113100", "Basic Application Confidentiality Profil"),
                ("113103", "Clean Graphics Option"),
                ("113103", "Retain Device Identity Option")]:
            sqdataset.append((
                ((0x0008, 0x0100), value, "CS"),
                ((0x0008, 0x0104), desc, "LO"),
                ((0x0008, 0x0102), "DCM", "CS")))
        add_dataelement(dataset, (0x0012, 0x0064), sqdataset, "SQ")

    # Check that all tags with 'VR' 'PN' has been anonymized
    # dataset.walk(callback_patient_name)


def callback_main(dataset, data_element):
    """ Called from the dataset 'walk' recursive function, will anonymize
    all DICOM fields by applying all the declared callbacks."""
    # Deal with sequence
    if data_element.VR == "SQ":
        for inner_dataset in data_element.value:
            anonymize_dataset(inner_dataset, level=2)

    # Deal with typed tags
    else:
        for pattern, callback in CALLBACKS.values():

            # Form kwargs
            kwargs = {
                "dataset": dataset,
                "data_element": data_element
            }
            if pattern is not None:
                kwargs["pattern"] = pattern

            # Call the callback
            if callback(**kwargs):
                break
