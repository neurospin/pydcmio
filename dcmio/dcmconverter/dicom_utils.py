#! /usr/bin/env python
##########################################################################
# CAPS - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
from __future__ import with_statement
import os
import json
import dicom
import nibabel
import glob
import numpy

# Dcmio import
from dcmio.dcmreader.dcmreader import get_repetition_time


def generate_config(output_directory):
    """ Generate a dcm2nii configuration file that disable the interactive
    mode.

    <unit>
        <input name="output_directory" type="Directory" description="The
            destination folder."/>
        <output name="config_file" type="File" description="A dcm2nii
            configuration file."/>
    </unit>
    """
    if not os.path.isdir(output_directory):
        os.makedirs(output_directory)
    config_file = os.path.join(output_directory, "config.ini")
    open_file = open(config_file, "w")
    open_file.write("[BOOL]\nManualNIfTIConv=0\n")
    open_file.close()
    return config_file


def add_meta_to_nii(nii_files, dicom_dir, prefix, dcm_tags, output_directory,
                    additional_information=[]):
    """ Add dicom tags to Nifti1 image type header.

    All selected dicom tags values are set in the 'descrip' nifti header
    field.

    <unit>
        <input name="nii_files" type="List" content="File" description="The
            nifti images to fill."/>
        <input name="dicom_dir" type="Directory" description="The directory
            containing the dicoms used to generate the nifti image."/>
        <input name="prefix" type="String" description="The output image name
            prefix."/>
        <input name="dcm_tags" type="List"
            content="Tuple_Str_List_Tuple_Str_Str"
            description="A list of 2-uplet of the form (name, tag) that will
            be inserted in the 'descrip' nifti header field."/>
        <input name="output_directory" type="Directory" description="The
            destination folder."/>
        <input name="additional_information" type="List"
            content="Tuple_Str_Str" description="A free dictionary items to be
            inserted in the 'descrip' image header field."/>
        <output name="filled_nii_files" type="List" content="File"
            description="The nifti images containing the filled header."/>
    </unit>
    """
    # Load a dicom image
    dicom_files = glob.glob(os.path.join(dicom_dir, "*.dcm"))
    dcmimage = dicom.read_file(dicom_files[0], force=True)

    # Go through all nifti files
    filled_nii_files = []
    for nii_file in nii_files:

        # Load the nifti1 image
        image = nibabel.load(nii_file)

        # Check that we have a nifti1 format image
        if isinstance(image, nibabel.nifti1.Nifti1Image):

            # Create the destination image path
            if not os.path.isdir(output_directory):
                os.makedirs(output_directory)
            filled_nii_file = os.path.join(
                output_directory, prefix + "_" + os.path.basename(nii_file))

            # Fill the nifti1 header
            header = image.get_header()

            # > slice_duration: Time for 1 slice
            repetition_time = get_repetition_time(dicom_files[0])
            if repetition_time is not None:
                repetition_time = float(repetition_time)
                header.set_dim_info(slice=2)
                nb_slices = header.get_n_slices()
                slice_duration = round(repetition_time / nb_slices, 0)
                header.set_slice_duration(slice_duration)

            # > add free dicom fields
            # extract value from the dicom file
            content = {}
            for name, tag in dcm_tags:

                try:
                    # enhances storage, the value is burried under one or
                    # several layer(s) of sequence
                    current_dataset = dcmimage
                    if len(tag) > 1:
                        for inner_tag in tag[:-1]:
                            seq_field = current_dataset[inner_tag]
                            current_dataset = seq_field.value[0]
                    last_tag = tag[-1]
                    content[str(name)] = str(current_dataset[last_tag].value)
                except:
                    pass

            # > add/update content
            for key, value in additional_information:
                content[key] = value
            free_field = numpy.array(json.dumps(content),
                                     dtype=header["descrip"].dtype)
            image.get_header()["descrip"] = free_field

            # Update the image header
            image.update_header()

            # Save the filled image
            nibabel.save(image, filled_nii_file)
            filled_nii_files.append(filled_nii_file)

        # Unknwon image format
        else:
            raise Exception(
                "Only Nifti1 image are supported not '{0}'.".format(
                    type(image)))

    return filled_nii_files
