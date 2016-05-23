##########################################################################
# NSAP - Copyright (C) CEA, 2015
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
import dicom


def repr_dataelement(data_element):
    """ Compute the representation of a data element.

    Parameters
    ----------
    data_element: dicom.dataset.DataElement (mandatory)
        a data element to be represented.

    Returns
    -------
    desc: list of str
        the represnetation of the input data element.
    """
    desc = []
    if data_element.VR == "SQ":
        for inner_dataset in data_element.value:
            inner_desc = []
            for inner_tag, innerdata_element in inner_dataset.items():
                inner_repr = repr_dataelement(innerdata_element)
                if isinstance(inner_repr, list):
                    inner_repr = repr(inner_repr)
                inner_desc.append([inner_tag, inner_repr])
            desc.append(inner_desc)
    else:
        desc = repr(data_element.value)
    return desc


def add_dataelement(dataset, tag, value, VR=None):
    """ Update or add a new tag.

    Parameters
    ----------
    dataset: Dataset (mandatory)
        a pydicom DICOM dataset.
    tag: 2-uplet (mandatory)
        a DICOM tag.
    value: str or number (mandatory)
        the actual value.
    VR: str (optional, default None)
        the DICOM value representation: expected if the tag does not exist in
        the current dataset.
    """
    if tag in dataset:
        dataset[tag].value = value
    elif VR is "SQ":
        sequence = []
        for sqvalue in value:
            sqdataset = dicom.dataset.Dataset()
            for sqtag, sqvalue, sqVR in sqvalue:
                add_dataelement(sqdataset, sqtag, sqvalue, sqVR)
            sequence.append(sqdataset)
        element = dicom.dataset.DataElement(tag, VR, sequence)
        dataset.add(element)
    elif VR is not None:
        element = dicom.dataset.DataElement(tag, VR, value)
        dataset.add(element)
    else:
        raise Exception("A VR is expected when the tag to insert does not "
                        "exist in the current dataset.")


def replace_by(value, VR, action,
               default_name="John Doe",
               default_date="18000101",
               default_datetime="180001010000.000000",
               default_time="0000.000000",
               default_text="anon",
               default_code="ANON",
               default_age="000M",
               default_decimal="0.0",
               default_integer="0",
               default_uid="000.000.0"):
    """ Replace a 'value' depending of the input 'action' and the value
    representation 'VR'.

    The following action codes are:

    * D - replace with a non zero length value that may be a dummy value and
      consistent with the VR
    * Z - replace with a zero length value, or a non-zero length value that
      may be a dummy value and consistent with the VR
    * X - remove
    * K - keep (unchanged for non-sequence attributes, cleaned for sequences)
    * C - clean, that is replace with values of similar meaning known not to
      contain identifying information and consistent with the VR
    * U - replace with a non-zero length UID that is internally consistent
      within a set of Instances
    * Z/D - Z unless D is required to maintain IOD conformance (Type 2 versus
      Type 1)
    * X/Z - X unless Z is required to maintain IOD conformance (Type 3 versus
      Type 2)
    * X/D - X unless D is required to maintain IOD conformance (Type 3 versus
      Type 1)
    * X/Z/D - X unless Z or D is required to maintain IOD conformance (Type 3
      versus Type 2 versus Type 1)
    * X/Z/U* - X unless Z or replacement of contained instance UIDs (U) is
      required to maintain IOD conformance (Type 3 versus Type 2 versus Type 1
      sequences containing UID references)

    We use here the PS 3.6 convention.
    """
    if action in ["X", "X/Z", "X/D", "X/Z/D", "X/Z/U*"]:
        return None
    elif action in ["U", "D", "Z", "Z/D"]:
        if VR == "DA":
            return default_date
        elif VR == "AS":
            return default_age
        elif VR == "DS":
            return default_decimal
        elif VR == "DT":
            return default_datetime
        elif VR == "TM":
            return default_time
        elif VR == "FL":
            return float(eval(default_decimal))  # numpy.float32
        elif VR == "FD":
            return float(eval(default_decimal))  # numpy.float64
        elif VR in ["IS"]:
            return default_integer
        elif VR in ["UL", "US", "SS", "SL"]:
            return eval(default_integer)
        elif VR == "PN":
            return default_name
        elif VR == "UI":
            return default_uid
        elif VR == "CS":
            return default_code
        elif VR in ["LO", "LT", "ST", "SH"]:
            return default_text
        elif VR in ["OB", "OW"]:
            return default_integer
        else:
            raise Exception("VR '{0}' is not yet supported. Current value is "
                            "'{1}'.".format(VR, value))
    else:
        raise Exception("Action '{0}' is not yet supported.".format(action))
