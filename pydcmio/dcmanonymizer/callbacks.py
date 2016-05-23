##########################################################################
# NSAP - Copyright (C) CEA, 2015
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# Dcmio import
from .utils import replace_by
from .utils import repr_dataelement

# Define global log variable
ANON_LOG = {}
MANUFACTURER = []
CALLBACKS = {}
TAGS = {}
PRIVATE_DEIDENTIFY = {}


def callback_private(dataset, data_element):
    """ Called from the dataset 'walk' recursive function, will anonymize
    all the private fields."""
    # Deal with private tags only
    if data_element.tag.is_private:

        # Check if this private tag needs to be removed
        tag_repr = repr(data_element.tag)[1:-1].replace(" ", "")
        keep_private_tag = False
        for pattern in PRIVATE_DEIDENTIFY[MANUFACTURER[0]]:
            if pattern.match(tag_repr):
                keep_private_tag = True
                break

        # Remove tag if requested
        if not keep_private_tag:
            dataset.pop(data_element.tag)
            value = data_element.value
            anon_value = replace_by(value, data_element.VR, "X")
            value_repr = repr_dataelement(data_element)
            ANON_LOG.setdefault(tag_repr, []).append((value_repr, anon_value))
        else:
            print(tag_repr, repr_dataelement(data_element))

        return True

    return False


def callback_tag(dataset, data_element, pattern):
    """ Called from the dataset 'walk' recursive function, will anonymize
    all the tag 'tag'."""
    tag, action = pattern
    if tag in dataset:
        tag_repr = repr(data_element.tag)[1:-1].replace(" ", "")
        value = data_element.value
        anon_value = replace_by(value, data_element.VR, action)
        value_repr = repr_dataelement(data_element)
        ANON_LOG.setdefault(tag_repr, []).append((value_repr, anon_value))
        if anon_value is None:
            dataset.pop(data_element.tag)
        else:
            data_element.value = anon_value

        return True

    return False


def callback_xxxx(dataset, data_element, pattern):
    """ Called from the dataset 'walk' recursive function, will anonymize
    all the '50xx,xxx' fields."""
    tag_repr = repr(data_element.tag)[1:-1].replace(" ", "")

    if pattern.match(tag_repr):
        value = data_element.value
        anon_value = replace_by(value, data_element.VR, "X")
        value_repr = repr_dataelement(data_element)
        ANON_LOG.setdefault(tag_repr, []).append((value_repr, anon_value))
        if anon_value is None:
            dataset.pop(data_element.tag)
        else:
            data_element.value = anon_value

        return True

    return False


def callback_patient_name(dataset, data_element):
    """ Called from the dataset 'walk' recursive function, will set
    a new identitiy to the subject."""
    tag_repr = repr(data_element.tag)[1:-1].replace(" ", "")
    if data_element.VR == "PN":
        if tag_repr not in ANON_LOG:
            raise Exception("Tag '({0})' contains patient information and "
                            "has not been anonymized.".format(tag_repr))
