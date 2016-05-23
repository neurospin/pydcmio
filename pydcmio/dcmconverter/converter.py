##########################################################################
# NSAp - Copyright (C) CEA, 2013 - 2016
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
import os
import re
import json
import dicom
import nibabel
import numpy

# Dcmio import
from pydcmio.dcmreader.reader import get_values
from pydcmio.dcmreader.reader import walk
from pydcmio.dcm2nii.wrapper import Dcm2NiiWrapper


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
    add_date: str (optional, default True)
        If 'True' then dcm2nii will add the requested element in the output
        filename.
    add_acquisition_number: str (optional, default True)
        If 'True' then dcm2nii will add the requested element in the output
        filename.
    add_protocol_name: str (optional, default True)
        If 'True' then dcm2nii will add the requested element in the output
        filename.
    add_patient_name: str (optional, default True)
        If 'True' then dcm2nii will add the requested element in the output
        filename.
    add_source_filename: str (optional, default True)
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

    You can specify all the 'dcm2nii' command options as input function
    parameters.

    The basic usage is:
    dcm2nii <options> <sourcenames>

    Options:
    a Anonymize [remove identifying information]: Y,N = Y
    b load settings from specified inifile, e.g. '-b C:\set\t1.ini'
    d Date in filename [filename.dcm -> 20061230122032.nii]: Y,N = N
    e events (series/acq) in filename [filename.dcm -> s002a003.nii]: Y,N = N
    f Source filename [e.g. filename.par -> filename.nii]: Y,N = N
    g gzip output, filename.nii.gz [ignored if '-n n']: Y,N = Y
    i ID  in filename [filename.dcm -> johndoe.nii]: Y,N = N
    n output .nii file [if no, create .hdr/.img pair]: Y,N = Y
    o Output Directory, e.g. 'C:\TEMP' (if unspecified, source directory
    is used)
    p Protocol in filename [filename.dcm -> TFE_T1.nii]: Y,N = Y
    r Reorient image to nearest orthogonal: Y,N
    s SPM2/Analyze not SPM5/NIfTI [ignored if '-n y']: Y,N = N
    t Text report (patient and scan details): Y,N = N
    v Convert every image in the directory: Y,N = Y
    x Reorient and crop 3D NIfTI images: Y,N = N

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
    if not os.path.isfile(b):
        raise ValueError("'{0}' is not a valid configuration file.".format(b))
    with open(b, "rt") as open_file:
        lines = open_file.readlines()
    outdirs = [line.replace("OutDir=", "") for line in lines
               if line.startswith("OutDir=")]
    if len(outdirs) != 1:
        raise ValueError("Expect one destination folder ('OutDir=') in "
                         "configuration file '{0}'.".format(b))
    niidir = outdirs[0].rstrip("\n")

    # Call dcm2nii
    dcm2niiprocess = Dcm2NiiWrapper("dcm2nii")
    dcm2niiprocess(cmd=["dcm2nii", "-o", o, "-b", b, input])

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


def add_meta_to_nii(nii_file, dicom_dir, dcm_tags, outdir, prefix="f",
                    additional_information=None):
    """ Add dicom tags to Nifti1 image header.

    All selected dicom tag values are set in the 'descrip' Nifti header
    field.

    Parameters
    ----------
    nii_file: str
        The nifti image to fill.
    dicom_dir: str
        The directory containing the dicoms used to generate the nifti image.
        We assume here that this folder contains only Dicom files.
    dcm_tags: list
        A list of 3-uplet of the form (name, tag, stack_values) that will
        be inserted in the 'descrip' Nifti header field. If we want to stack
        all the Dicom dataset values, the 'stack_values' option mist be set to
        True.
    outdir: str
        The destination folder.
    prefix: str (optional, default 'f')
        The output image name prefix.
    additional_information: dict (optional, default None)
        A free dictionary items to be inserted in the 'descrip' image
        header field.

    Returns
    -------
    filled_nii_file: str
        The nifti image with filled header.
    """
    # Set default
    if additional_information is None:
        additional_information = {}

    # Create the destination image path
    if not os.path.isdir(outdir):
        os.makedirs(outdir)

    # Load the first listed dicom image
    dicom_files = os.listdir(dicom_dir)
    dataset = dicom.read_file(os.path.join(dicom_dir, dicom_files[0]),
                              force=True)

    # Load the nifti1 image
    niiimage = nibabel.load(nii_file)

    # Check that we have a nifti1 format image
    filled_nii_file = os.path.join(outdir, prefix + os.path.basename(nii_file))
    if isinstance(niiimage, nibabel.nifti1.Nifti1Image):

        # Fill the nifti1 header
        header = niiimage.get_header()

        # > slice_duration: Time for 1 slice
        repetition_time = get_values(dataset, "get_repetition_time")
        if repetition_time is not None and len(niiimage.shape) > 2:
            repetition_time = float(repetition_time)
            header.set_dim_info(slice=2)
            nb_slices = header.get_n_slices()
            slice_duration = round(repetition_time / nb_slices, 0)
            header.set_slice_duration(slice_duration)

        # > add free dicom fields
        # enhances storage: the value is burried under one or several layer(s)
        # of sequence
        content = {}
        for name, tag, stack_values in dcm_tags:
            content[str(name)] = walk(dataset, tag, stack_values=stack_values)

        # > add/update free content
        content.update(additional_information)

        # Overwrite the 'descrip' header filed
        free_field = numpy.array(json.dumps(content),
                                 dtype=header["descrip"].dtype)
        niiimage.get_header()["descrip"] = free_field

        # Update the image header
        niiimage.update_header()

        # Save the filled image
        nibabel.save(niiimage, filled_nii_file)

    # Unknwon image format
    else:
        raise ValueError(
            "'{0}' is not a Nifti1 image but a '{1}' image.".format(
                nii_file, type(niiimage)))

    return filled_nii_file
