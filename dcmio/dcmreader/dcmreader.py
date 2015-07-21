#! /usr/bin/env python
# -*- coding: utf-8 -*-
##########################################################################
# NSAP - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# Diverse dicom reading functions to extract precise information

import dicom
import os
import logging


# dataset Walker (to browse enhanced dicom efficiently)
def walk(dataset, callback, _tag):
    taglist = sorted(dataset.keys())
    for tag in taglist:
        data_element = dataset[tag]
        out = callback(dataset, data_element, _tag)
        if tag in dataset and data_element.VR == "SQ":
            sequence = data_element.value
            for sub_dataset in sequence:
                out = walk(sub_dataset, callback, _tag)
        if out:
            return out

    return None


def walker_callback(dataset, data_element, _tag):
    """Called from the dataset "walk" recursive function for
    all data elements."""
    if data_element.tag == _tag:
        return data_element.value
    return None


def get_repetition_time(path_to_dicom):
    """
    return the repetition time as string
    """
    dataset = dicom.read_file(path_to_dicom, force=True)
    tr = walk(dataset, walker_callback, (0x0018, 0x0080))
    if tr:
        # convert in ms
        if tr < 1000:
            tr *= 1000.
        return "{0}".format(tr)
    return '0'


def get_date_scan(path_to_dicom):
    """
    return session date as string
    """
    dataset = dicom.read_file(path_to_dicom, force=True)
    value = walk(dataset, walker_callback, (0x0008, 0x0022))
    if value:
        return value
    return '0'


def get_echo_time(path_to_dicom):
    """
    return echo time
    """
    dataset = dicom.read_file(path_to_dicom, force=True)
    value = walk(dataset, walker_callback, (0x0018, 0x0081))
    if value:
        return value
    return -1


def get_SOP_storage_type(path_to_dicom):
    """
    return True for Enhanced storage, False otherwise
    """
    dataset = dicom.read_file(path_to_dicom, force=True)
    value = walk(dataset, walker_callback, (0x0008, 0x0016))
    if value:
        if "Enhanced" in str(value):
            return True
    return False


def get_Raw_Data_Run_Number(path_to_dicom):
    """
    return value field
    WARNING: private field: designed for GE scan (LONDON IOP centre)
    """
    dataset = dicom.read_file(path_to_dicom, force=True)
    value = walk(dataset, walker_callback, (0x0019, 0x10a2))
    if value:
        return value
    return -1


def get_sequence_number(path_to_dicom):
    """
    return sequence Number
    """
    dataset = dicom.read_file(path_to_dicom, force=True)
    value = walk(dataset, walker_callback, (0x0020, 0x0011))
    if value:
        return value
    return '0'


def get_nb_slices(path_to_dicom):
    """
    Return number of slices (ImagesInAcquisition)
    """
    dataset = dicom.read_file(path_to_dicom, force=True)
    value = walk(dataset, walker_callback, (0x0020, 0x1002))
    if value:
        return int(value)
    else:
        value = walk(dataset, walker_callback, (0x2001, 0x1018))
        if value:
            return int(value)
    return 0


def get_nb_temporal_position(path_to_dicom):
    """
    Get number of volumes
    """
    dataset = dicom.read_file(path_to_dicom, force=True)
    value = walk(dataset, walker_callback, (0x0020, 0x0105))
    if value:
        return int(value)
    return 0


def get_sequence_name(path_to_dicom):
    """
    get sequence name and format it
    """
    dataset = dicom.read_file(path_to_dicom, force=True)
    value = walk(dataset, walker_callback, (0x0008, 0x103e))
    if value:
        return value.replace(" ", "_")
    return "unknown"


def get_protocol_name(path_to_dicom):
    """
    get protocol name
    """

    dataset = dicom.read_file(path_to_dicom, force=True)
    value = walk(dataset, walker_callback, (0x0018, 0x1030))
    if value:
        return value.replace(" ", "_")
    return "unknown"


def get_serie_serieInstanceUID(path_to_dicom):
    """
    serie UID number
    """
    dataset = dicom.read_file(path_to_dicom, force=True)
    value = walk(dataset, walker_callback, (0x0020, 0x000e))
    if value:
        return value.replace(" ", "_")
    return "unknown"


def get_number_of_slices_philips(path_to_dicom):
    """ return value of "NumberOfSlicesMR" field
    """
    try:
        # run dcmdump and read number of slices inside. pydicom is unable
        # to extract the information
        temporary_text_file = os.path.join(os.path.dirname(path_to_dicom),
                                           "temp.txt")
        os.system("dcmdump {0} > {1}".format(path_to_dicom,
                                             temporary_text_file))
        # load text file
        buff = open(temporary_text_file, "r")
        for line in buff.readlines():
            if "StackNumberOfSlices" in line:
                temp = line
                break
        buff.close()
        # Remove temp file
        os.remove(temporary_text_file)
        # Now we have the line, remove spaces
        value = temp.replace(' ', '')
        # return the last 2 character as integer (we assume that there will
        # always be more than 9 slices)
        return int(value.split('#')[0][-2:])
    except:
        logging.warning("WARNING: no 'NumberOfSlicesMR' field")
        return 0
