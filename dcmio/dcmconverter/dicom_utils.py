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
import matplotlib
from collections import OrderedDict

# Set matplotlib backend
matplotlib.use("AGG")

from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt


def multi_snaps(image_files, nb_snaps, nb_volumes, nb_snaps_per_page, output_directory):
    """ Slice a Volume

    Generate an image with merge sagittal, axial, and coronal slices.

    <process>
        <return name="snap_files" type="List_File" desc="Path to the resulting snp
            images."/>
        <input name="image_files" type="List_File" desc="Volumes to slice."/>
        <input name="nb_snaps" type="Int" desc="The desired number of
            snapshots."/>
        <input name="nb_volumes" type="Int" desc="The desired number of
            volumes sanped in the time domain."/>
        <input name="nb_snaps_per_page" type="Int" desc="The desired number of
            sanps per page."/>
        <input name="output_directory" type="Directory" desc="The destination
            folder."/>
    </process>
    """
    # Go through all nifti files
    snap_files = []
    for fname in image_files:

        # Load the nifti image
        image = nibabel.load(fname)
        data = image.get_data()
        ndims = len(image.shape)
        tslices = OrderedDict()

        # Case 3d + t images
        if ndims == 4:
            for time_index in numpy.round(numpy.linspace(
                                            0, image.shape[3] - 1, nb_volumes)):
                tslices[time_index] = get_3d_volume_slices(
                    data[..., time_index], nb_snaps)
        # Case 3d image
        elif ndim == 3:
            tslices[0] = get_3d_volume_slices(data, nb_snaps)
        # Not implemented error
        else:
            raise NotImplementedError(
                "Can't deal with image of dim '{0}'".format(ndims))

        # Create an image with all the slices displayed
        # Create the PdfPages object to which we will save the slices
        snap_files.append(os.path.join(output_directory, "{0}.pdf".format(
            os.path.basename(fname).split(".")[0])))
        pdf = PdfPages(snap_files[-1])
        try:
            for t_index, slices in tslices.iteritems():

                x_slices, y_slices, z_slices = slices
                for cut in range(nb_snaps):
        
                    # Create the figure
                    row_index = cut % nb_snaps_per_page
                    if row_index == 0:
                        fig = plt.figure()

                    # Plot the axial coronal sagital slices
                    ax = plt.subplot(nb_snaps_per_page, 3, row_index * 3 + 1)
                    ax.imshow(x_slices[cut], cmap="gray", aspect="equal")
                    ax.axes.get_xaxis().set_visible(False)
                    ax.axes.get_yaxis().set_visible(False)
                    ax = plt.subplot(nb_snaps_per_page, 3, row_index * 3 + 2)
                    ax.imshow(y_slices[cut], cmap="gray", aspect="equal")
                    ax.axes.get_xaxis().set_visible(False)
                    ax.axes.get_yaxis().set_visible(False)
                    ax = plt.subplot(nb_snaps_per_page, 3, row_index * 3 + 3)
                    ax.imshow(z_slices[cut], cmap="gray", aspect="equal")
                    ax.axes.get_xaxis().set_visible(False)
                    ax.axes.get_yaxis().set_visible(False)

                    # Saves the current rows into a pdf page
                    if row_index == (nb_snaps_per_page - 1):
                        plt.suptitle("{0}, {1}".format(os.path.basename(fname),
                                                       int(t_index)))
                        pdf.savefig(fig)
                        plt.close()

                # Close current page before treating a new volume
                plt.suptitle("{0}, {1}".format(os.path.basename(fname),
                                            int(t_index)))
                pdf.savefig(fig)
                plt.close()

            # Close the pdf
            pdf.close()

        except:
            pdf.close()
            raise
            

    return snap_files


def get_3d_volume_slices(volume, nb_snaps):
    """ Slice a 3d volume.

    Parameters
    ----------
    volume: array [X, Y, Z]
        the volume to slice.
    nb_snaps: int
        the number of slices that will be extracted in each direction.

    Returns
    -------
    x_slices, y_slices, z_slices: list of array [X, Y]
        the selected slices in all space directions.
    """
    # Slice along the x-axis
    line_cuts = numpy.round(numpy.linspace(0, volume.shape[0] - 1, nb_snaps))
    # Get the corresponding slices
    x_slices = [volume[cut, :, :] for cut in line_cuts]

    # Slice along the y-axis
    line_cuts = numpy.round(numpy.linspace(0, volume.shape[1] - 1, nb_snaps))
    # Get the corresponding slices
    y_slices = [volume[:, cut, :] for cut in line_cuts]

    # Slice along the z-axis
    line_cuts = numpy.round(numpy.linspace(0, volume.shape[2] - 1, nb_snaps))
    # Get the corresponding slices
    z_slices = [volume[:, :, cut] for cut in line_cuts]

    return (x_slices, y_slices, z_slices)


def generate_config(output_directory):
    """ Generate a dcm2nii configuration file that disable the interactive
    mode.

    <process>
        <return name="config_file" type="File" desc="A dcm2nii configuration
            file."/>
        <input name="output_directory" type="Directory" desc="The destination
            folder."/>
    </process>
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

    <process>
        <return name="filled_nii_files" type="List_File" desc="The nifti image
            containing the filled header."/>
        <input name="nii_files" type="List_File" desc="The nifti image to fill."/>
        <input name="dicom_dir" type="Directory" desc="The directory containing
            the dicoms used to generate the nifti image."/>
        <input name="prefix" type="String" desc="The output image name prefix."/>
        <input name="dcm_tags" type="List_Tuple_Str_Tuple_Str_Str" desc="A list of
            2-uplet of the form (name, tag) that will be inserted in the
            'descrip' nifti header field."/>
        <input name="output_directory" type="Directory" desc="The destination
            folder."/>
    </process>
    """
    # Go through all nifti files
    filled_nii_files = []
    for nii_file in nii_files:

        # Load the nifti1 image
        image = nibabel.load(nii_file)

        # Load a dicom image
        dicom_files = glob.glob(os.path.join(dicom_dir, "*.dcm"))
        dcmimage = dicom.read_file(dicom_files[0])

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
            repetition_time = float(dcmimage[('0x0018', '0x0080')].value)
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

            return filled_nii_files

        # Unknwon image format
        else:
            raise Exception(
                "Only Nifti1 image are supported not '{0}'.".format(type(image)))

