##########################################################################
# NSAp - Copyright (C) CEA, 2013 - 2016
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

"""
Parse private Siemens CSA2 header field.
"""

# System import
import os
import ast
import dicom
import struct


def get_siemens_csa2_header(dataset_or_dcmpath):
    """ Return a dictionary with the Siemens CSA2 Header.

    Parameters
    ----------
    dataset_or_dcmpath: dataset or str (mandatory)
        a pydicom dataset structure or a path to a valid Dicom file.

    Returns
    -------
    content: dict
        a dictionnary containing the Siemens CSA2 header as (tag, values)
        items.
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

    # Get the csa2 header representation
    content = None
    for tag in [(0x0029, 0x1010), (0x0029, 0x1020), (0x0029, 0x1210),
                (0x0029, 0x1110)]:
        if tag in dataset:
            content = parse_csa2(dataset[tag])
            break

    return content


def parse_csa2(csa):
    """ Return a dictionary with the Siemens CSA2 Header.

    Siemens CSA Header tag is (0x0029, 0x1020).
    See also http://nipy.org/nibabel/dicom/siemens_csa.html.

    Parameters
    ----------
    csa: binary (mandatory)
        the Siemens CSA2 Header.

    Returns
    -------
    content: dict
        a dictionnary containing the Siemens CSA2 header as (tag, values)
        items.
    """
    format = ("<"   # Little-endian
              "4s"  # SV10
              "4s"  # \x04\x03\x02\x01
              "I"   # Number of items
              "I"   # Unknown
              )
    size = struct.calcsize(format)

    version, _, number_of_elements, _ = struct.unpack(format, csa[:size])

    start = size
    content = {}
    for _ in range(number_of_elements):
        (name, items), size = parse_element(csa, start)
        content[name] = items
        start += size

    return content


def parse_element(csa, start):
    """ Return a pair (name, items), total_size.

    See also http://nipy.org/nibabel/dicom/siemens_csa.html.
    """
    format = ("<"    # Little endian
              "64s"  # Name
              "I"    # VM
              "2s"   # VR
              "2s"   # Unknown (end of VR ?)
              "I"    # Syngo datatype
              "I"    # Number of items
              "I"    # Unknown
              )
    size = struct.calcsize(format)

    name, vm, vr, _, syngo_datatype, number_of_items, _ = struct.unpack(
        format, csa[start:start + size])
    name = name.split("\x00")[0]

    total_size = size
    start += size
    items = []
    for i in range(number_of_items):
        item, size = parse_item(csa, start)
        if i < vm:
            if vr in ["DS", "FL", "FD"]:
                item = float(item[:-1])
            elif vr in ["IS", "SS", "US", "SL", "UL"]:
                item = int(item[:-1])
            else:
                try:
                    item = ast.literal_eval(item)
                except:
                    pass
            items.append(item)
        start += size
        total_size += size

    return (name, items), total_size


def parse_item(csa, start):
    """ Return a pair content, size.

    See also http://nipy.org/nibabel/dicom/siemens_csa.html.
    """
    format = ("<"   # Little endian
              "4I"  # Length
              )
    header_size = struct.calcsize(format)

    length = struct.unpack(format, csa[start:start + header_size])

    format = ("<"     # Little endian
              "{0}s"  # Content
              "{1}s"  # Padding (?)
              ).format(length[1], (4 - length[1] % 4) % 4)
    content_size = struct.calcsize(format)
    content, padding = struct.unpack(
        format,
        csa[start + header_size:start + header_size + content_size])

    return content, header_size + content_size
