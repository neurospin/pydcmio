##########################################################################
# NSAp - Copyright (C) CEA, 2013 - 2016
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

"""
Diverse Dicom reading functions to extract precise information.
"""

# System import
import dicom
import os


# Map known request: name: (tag, stack_values)
STANDARD_EXTRACTOR = {
    "get_phase_encoding": ((0x0018, 0x1312), False),
    "get_b_vectors": ((0x0018, 0x9089), True),
    "get_b_values": ((0x0018, 0x9087), True),
    "get_repetition_time": ((0x0018, 0x0080), False),
    "get_date_scan": ((0x0008, 0x0022), False),
    "get_echo_time": ((0x0018, 0x0081), False),
    "get_all_sop_instance_uids": ((0x0008, 0x1155), True),
    "get_sop_storage_type": ((0x0008, 0x0016), False),
    "get_sequence_number": ((0x0020, 0x0011), False),
    "get_nb_slices": ((0x0020, 0x1002), False),
    "get_nb_temporal_position": ((0x0020, 0x0105), False),
    "get_manufacturer_name": ((0x0008, 0x0070), False),
    "get_manufacturer_model_name": ((0x0008, 0x1090), False),
    "get_sequence_name": ((0x0008, 0x103e), False),
    "get_protocol_name": ((0x0018, 0x1030), False),
    "get_serie_instance_uid": ((0x0020, 0x000e), False)
}

# Map to known private tags
PRIVATE_FIELDS = {
    "get_phase_encoding": [],
    "get_b_vectors": [],
    "get_b_values": [],
    "get_repetition_time": [],
    "get_date_scan": [],
    "get_echo_time": [],
    "get_all_sop_instance_uids": [],
    "get_sop_storage_type": [],
    "get_sequence_number": [],
    "get_nb_slices": [(0x2001, 0x102d), (0x2001, 0x1018)],
    "get_nb_temporal_position": [],
    "get_manufacturer_name": [],
    "get_manufacturer_model_name": [],
    "get_sequence_name": [],
    "get_protocol_name": [],
    "get_serie_instance_uid": []
}


def walk(dataset_or_dcmpath, tag, stack_values=False):
    """ Function to extract a tag associated value(s) from a Dicom dataset.

    .. note::

        Recusrive function is required as new enhanced storage presents only
        one Dicom containing several sub-sequence of fields.
        The walked is called on each sub-sequence.

    Parameters
    ----------
    dataset_or_dcmpath: dataset or str (mandatory)
        a pydicom dataset structure or a path to a valid Dicom file.
    tag: 2-uplet (mandatory)
        the Dicom tag of the field containing the value to extract.
    stack_values: bool (optional, default False)
        if set to True, returns all the detected occurences, otherwise the
        first occurence only.

    Returns
    -------
    values: list
        the tag associated value(s). None if the field has not been found in
        the dataset.
    """
    # Deal with input parameters
    if isinstance(dataset_or_dcmpath, str):
        if not os.path.isfile(dataset_or_dcmpath):
            raise ValueError("'{0}' is not a valid Dicom file.".format(
                dataset_or_dcmpath))
        dataset = dicom.read_file(dataset_or_dcmpath, force=True)
    else:
        if not isinstance(dataset_or_dcmpath, dicom.dataset.Dataset):
            raise ValueError("'{0}' is not a 'pydicom' Dataset.".format(
                dataset_or_dcmpath))
        dataset = dataset_or_dcmpath

    # Go through each dataset tags
    values = []

    # Case 1: the desired tag is accessbile in the current dataset level
    if tag in dataset:
        if dataset[tag].VR != "SQ":
            values.append(dataset[tag].value)
            if not stack_values:
                return values
        else:
            sequence = dataset[tag].value
            for sub_dataset in sequence:
                values.extend(
                    walk(dataset=sub_dataset, tag=tag,
                         stack_values=stack_values))
                if not stack_values and len(values) > 0:
                    return values

    # Case 2: go deeper and check tag in Dicom sequences
    for tag in dataset.keys():
        if dataset[tag].VR == "SQ":
            sequence = dataset[tag].value
            for sub_dataset in sequence:
                sub_values = walk(sub_dataset, tag, stack_values=stack_values)
                if sub_values is not None:
                    values.extend(sub_values)
                if not stack_values and len(values) > 0:
                    return values

    # Finally: if no match return None
    if len(values) == 0:
        values = None

    return values


def get_values(dataset_or_dcmpath, extractor):
    """ Get an extractor associated value(s).

    Parameters
    ----------
    dataset_or_dcmpath: dataset or str (mandatory)
        a pydicom dataset structure or a path to a valid Dicom file.
    extractor: str (mandatory)
        the name of the extractor specified in the 'STANDARD_EXTRACTOR'
        global variable.

    Returns
    -------
    values: list or an object
        the phase encoding (none if not found).
    """
    # Deal with input parameters
    if extractor not in STANDARD_EXTRACTOR:
        raise ValueError("'{0}' is not a valid extractor, registered "
                         "extractor are in {1}.".format(
                             extractor, STANDARD_EXTRACTOR.keys()))
    # Get tag associated values
    tag, stack_values = STANDARD_EXTRACTOR[extractor]
    values = walk(dataset_or_dcmpath, tag, stack_values=stack_values)
    if not stack_values and stack_values is not None:
        values = values[0]

    # Special cases
    if extractor == "get_repetition_time":
        # > convert in ms
        if values < 1000:
            values *= 1000.

    return values
