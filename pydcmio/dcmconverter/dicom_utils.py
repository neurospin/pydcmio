#! /usr/bin/env python
##########################################################################
# CAPS - Copyright (C) CEA, 2013 - 2016
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
from __future__ import with_statement
import os
import re
import json
import dicom
import nibabel
import glob
import numpy

# Dcmio import
from dcmio.dcmreader.dcmreader import get_repetition_time
from dcmio.extensions.dcm2nii import Dcm2NiiWrapper
from dcmio.extensions.dcm2nii.exceptions import Dcm2NiiRuntimeError
from dcmio.extensions.dcm2nii.exceptions import Dcm2NiiError

# Qap import
from qap.viz.plotting import plot_mosaic


def generate_config(niidir, anonymized=True, gzip=True, add_date=True,
                    add_acquisition_number=True, add_protocol_name=True,
                    add_patient_name=True, add_source_filename=True,
                    begin_clip=0, end_clip=0):
    """ Generate a dcm2nii configuration file that disable the interactive
    mode.

    Parameters
    ----------
    niidir: str
        The nifti destination folder.
    anonymized: bool (optional, default True)
        If 'True' then patient name will not be copied to NIfTI header.
    gzip: bool (optional, default True)
        If 'True' then dcm2nii will create compressed .nii.gz files.
    add_date, add_acquisition_number, add_protocol_name,
    add_patient_name, add_source_filename: str (optional, default True)
        If 'True' then dcm2nii will add the requested element in the output
        filename.
    begin_clip: int (optional, default 0)
        Specifies number of volumes to be removed from the beginning of a 4D
        acquisition.
    end_clip: int (optional, default 0)
        Specifies number of volumes to be removed from the end of a 4D
        acquisition.

    Returns
    -------
    config_file: str
        A dcm2nii configuration file written in the input 'niidir' folder.
    """
    # Check the the destination folder exists
    if not os.path.isdir(niidir):
        raise ValueError("'{0}' folder does not exists.".format(niidir))

    # Load the default configuration
    config_file = os.path.join(os.path.dirname(__file__),
                               "dcm2nii_config.json")
    with open(config_file, "r") as open_file:
        config = json.load(open_file)

    # Update the configuration
    config["BOOL"]["Anonymize"] = int(anonymized)
    config["BOOL"]["Gzip"] = int(gzip)
    config["BOOL"]["AppendDate"] = int(add_date)
    config["BOOL"]["AppendAcqSeries"] = int(add_acquisition_number)
    config["BOOL"]["AppendProtocolName"] = int(add_protocol_name)
    config["BOOL"]["AppendPatientName"] = int(add_patient_name)
    config["BOOL"]["AppendFilename"] = int(add_source_filename)
    config["INT"]["BeginClip"] = begin_clip
    config["INT"]["LastClip"] = end_clip
    config["INT"]["OutDirMode"] = 2
    config["STR"]["OutDir"] = niidir

    # Write the configuration file
    config_file = os.path.join(niidir, "dcm2nii.ini")
    with open(config_file, "w") as open_file:
        for section_name, config_items in config.items():
            open_file.write("[{0}]\n".format(section_name))
            for parameter_name, value in config_items.items():
                open_file.write("{0}={1}\n".format(parameter_name, value))

    return config_file


def dcm2nii(input, o, b):
    """ Dicom to nifti conversion using 'dcm2nii'.

    The basic usage is:
        dcm2nii <options> <sourcenames>
    Options:
        -a Anonymize [remove identifying information]: Y,N = Y
        -b load settings from specified inifile, e.g. '-b C:\set\t1.ini'
        -d Date in filename [filename.dcm -> 20061230122032.nii]: Y,N = N
        -e events (series/acq) in filename [filename.dcm -> s002a003.nii]: Y,N = N
        -f Source filename [e.g. filename.par -> filename.nii]: Y,N = N
        -g gzip output, filename.nii.gz [ignored if '-n n']: Y,N = Y
        -i ID  in filename [filename.dcm -> johndoe.nii]: Y,N = N
        -n output .nii file [if no, create .hdr/.img pair]: Y,N = Y
        -o Output Directory, e.g. 'C:\TEMP' (if unspecified, source directory is used)
        -p Protocol in filename [filename.dcm -> TFE_T1.nii]: Y,N = Y
        -r Reorient image to nearest orthogonal: Y,N
        -s SPM2/Analyze not SPM5/NIfTI [ignored if '-n y']: Y,N = N
        -t Text report (patient and scan details): Y,N = N
        -v Convert every image in the directory: Y,N = Y
        -x Reorient and crop 3D NIfTI images: Y,N = N

    Returns
    -------
    files: list of str
        the converted files in nifti format.
    reoriented_files: list of str
        the reoriented converted files in nifti format.
    reoriented_and_cropped_files list of str
        the reoriented and cropped converted files in nifti format.
    bvecs: list of str
        the diffusion directions.
    bvals: list of str
        the diffusion acquisiton b-values.
    """
    # Get the destination folder
    with open(b, "r") as open_file:
        lines = open_file.readlines()
    outdirs = [line.replace("OutDir=", "") for line in lines
               if line.startswith("OutDir=")]
    if len(outdirs) != 1:
        raise Dcm2NiiError("Expect one destination folder.")
    niidir = outdirs[0].rstrip("\n")

    # Call dcm2nii
    dcm2niiprocess = Dcm2NiiWrapper("dcm2nii")
    dcm2niiprocess()
    if dcm2niiprocess.exitcode != 0:
        raise Dcm2NiiRuntimeError(
            dcm2niiprocess.cmd[0], " ".join(dcm2niiprocess.cmd[1:]),
            dcm2niiprocess.stderr)

    # Format outputs: from nipype
    files = []
    reoriented_files = []
    reoriented_and_cropped_files = []
    bvecs = []
    bvals = []
    skip = False
    last_added_file = None
    for line in dcm2niiprocess.stdout.split("\n"):
        if not skip:
            out_file = None
            # For notgzipped detect files
            if line.startswith("Saving "):
                out_file = line[len("Saving "):]
            # For gzipped outputs files are not absolute
            elif line.startswith("GZip..."):
                out_file = os.path.abspath(
                    os.path.join(niidir, line[len("GZip..."):]))
            # For diffusion
            elif line.startswith("Number of diffusion directions "):
                if last_added_file:
                    base, filename = os.path.split(
                        last_added_file.replace(".gz", "").replace(".nii", ""))
                    bvecs.append(os.path.join(base, filename + ".bvec"))
                    bvals.append(os.path.join(base, filename + ".bval"))
            elif re.search('.*-->(.*)', line):
                val = re.search('.*-->(.*)', line)
                val = val.groups()[0]
                val = os.path.join(niidir, val)
                out_file = val

            if out_file:
                files.append(out_file)
                last_added_file = out_file
                continue

            if line.startswith("Reorienting as "):
                reoriented_files.append(line[len("Reorienting as "):])
                skip = True
                continue
            elif line.startswith("Cropping NIfTI/Analyze image "):
                base, filename = os.path.split(
                    line[len("Cropping NIfTI/Analyze image "):])
                filename = "c" + filename
                reoriented_and_cropped_files.append(
                    os.path.join(base, filename))
                skip = True
                continue
        skip = False

    return files, reoriented_files, reoriented_and_cropped_files, bvecs, bvals


def add_meta_to_nii(nii_files, dicom_dir, dcm_tags, output_directory,
                    prefix="filled", additional_information=None):
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
    # Set default
    if additional_information is None:
        additional_information = []

    # Load a dicom image
    dicom_files = os.listdir(dicom_dir)
    dcmimage = dicom.read_file(os.path.join(dicom_dir, dicom_files[0]),
                               force=True)

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
            repetition_time = get_repetition_time(os.path.join(dicom_dir,
                                                               dicom_files[0]))
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
                            if not seq_field.VR == "SQ":
                                raise Exception("the field {0} is not "
                                                "a sequence".format(inner_tag))
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


def mosaic(impath, outdir, strategy="average", indices=None, title=None):
    """ Create a snap of an input 3D or 4D image.

    If a 4D image is provided, select the 'index'th element or create an
    average volume.

    Parameters
    ----------
    impath: str
        the path to the image to slice.
    outdir: str
        the destination folder.
    strategy (optional, default 'average')
        in the case of 4d image the slice strategy: 'pick' or 'average'.
    indices (optional, default None)
        in the case of 4d image the indices of the volumes to average.

    Returns
    -------
    snap: str
        a 'pdf' snap of the desired volume.
    """
    # Check the strategy
    if strategy not in ["pick", "average"]:
        raise ValueError("Uknown '{0}' 4d strategy.".format(strategy))

    # Load the input image and apply the 4d strategy if necessary
    array = nibabel.load(impath).get_data()
    if len(array.dtype) > 0:
        array = numpy.asarray(array.tolist())
    shape = array.shape

    if array.ndim < 3 or array.ndim > 4:
        raise Exception("Only 3d or 4d images are accepted.")
    if array.ndim == 4 and strategy == "average":
        array = numpy.mean(array, axis=3)
    if array.ndim == 4 and strategy == "pick":
        try:
            array = numpy.mean(array[..., indices], axis=3)
        except:
            raise Exception("Can't pick volume indices '{0}' in array of shape "
                            "'{1}'.".format(indices, array.shape))

    # Create the snap with qap
    basename = os.path.basename(impath).split(".")[0]
    if title is None:
        title = basename
    else:
        basename = basename + "_" + title
    title += ": shape {0}".format(shape)
    snap = os.path.join(outdir, basename + ".pdf")
    fig = plot_mosaic(array, title=title)
    fig.savefig(snap, dpi=300)

    return snap


