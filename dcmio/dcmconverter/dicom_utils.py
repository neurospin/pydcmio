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
import dicom
import nibabel
import glob
import numpy


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


def add_meta_to_nii(nii_files, dicom_dir, prefix, dcm_tags, output_directory):
    """ Add slice duration and acquisition times to nifit1 image header.
    All selected dicom tags values are set in the description nifti header
    field.

    <unit>
        <input name="nii_files" type="List" content="File" description="The
            nifti images to fill."/>
        <input name="dicom_dir" type="Directory" description="The directory
            containing the dicoms used to generate the nifti image."/>
        <input name="prefix" type="String" description="The output image name
            prefix."/>
        <input name="dcm_tags" type="List" content="Tuple_Str_Tuple_Str_Str"
            description="A list of 2-uplet of the form (name, tag) that will
            be inserted in the 'descrip' nifti header field."/>
        <input name="output_directory" type="Directory" description="The
            destination folder."/>
        <output name="filled_nii_files" type="List" content="File"
            description="The nifti images containing the filled header."/>
    </unit>
    """
    # Load a dicom image
    dicom_files = glob.glob(os.path.join(dicom_dir, "*.dcm"))
    dcmimage = dicom.read_file(dicom_files[0])

    # Go through all nifti files
    filled_nii_files = []
    for nii_file in nii_files:

        # Load the nifti1 image
        image = nibabel.load(nii_file)

        # Check the we have a nifti1 format image
        if isinstance(image, nibabel.nifti1.Nifti1Image):

            # Create the destination image path
            if not os.path.isdir(output_directory):
                os.makedirs(output_directory)
            filled_nii_file = os.path.join(
                output_directory, prefix + "_" + os.path.basename(nii_file))

            # Fill the nifti1 header
            header = image.get_header()

            # > slice_duration: Time for 1 slice
            repetition_time = float(dcmimage[("0x0018", "0x0080")].value)
            header.set_dim_info(slice=2)
            nb_slices = header.get_n_slices()
            # Force round to 0 digit after coma. If more, nibabel completes to
            # 6 digits with random numbers...
            slice_duration = round(repetition_time / nb_slices, 0)
            header.set_slice_duration(slice_duration)

            # > add free dicom fields
            content = ["{0}={1}".format(name, dcmimage[tag].value)
                       for name, tag in dcm_tags]
            free_field = numpy.array(";".join(content),
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
