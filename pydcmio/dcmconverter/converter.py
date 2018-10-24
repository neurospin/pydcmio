##########################################################################
# NSAp - Copyright (C) CEA, 2013 - 2016
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

"""
Module that provides tools to convert DICOM files.
"""


# System import
from __future__ import print_function
import os
import re
import json
import time

# Third party import
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


def dcm2niix(input, o, f="%p", z="y", b="y"):
    """ Dicom to nifti conversion using 'dcm2nii'.

    You can specify all the 'dcm2niix' command options as input function
    parameters.

    The basic usage is:
    dcm2niix [options] <in_folder>

    Options:
    b: BIDS sidecar (y/n/o, default n)
    f: filename (%a=antenna  (coil) number, %c=comments, %d=description,
    %e echo number, %f=folder name, %i ID of patient, %m=manufacturer,
    %n=name of patient, %p=protocol, %s=series number, %t=time,
    %u=acquisition number, %z sequence name; default '%f_%p_%t_%s')
    h: show help
    m: merge 2D slices from same series regardless of study time, echo,
    coil, orientation, etc. (y/n, default n)
    o: output directory (omit to save to input folder)
    s: single file mode, do not convert other images in folder
    (y/n, default n)
    t: text notes includes private patient details (y/n, default n)
    v: verbose (y/n, default n)
    x: crop (y/n, default n)
    z: gz compress images (y/i/n, default n) [y=pigz, i=internal, n=no]


    Returns
    -------
    files: list of str
        the converted files in nifti format.
    bvecs: list of str
        the diffusion directions.
    bvals: list of str
        the diffusion acquisiton b-values.
    bids: str
        BIDS sidecar.
    """
    # Call dcm2nii
    dcm2niiprocess = Dcm2NiiWrapper("dcm2niix")
    dcm2niiprocess(cmd=["dcm2niix", "-o", o, "-f", f, "-z", z, "-ba", b,
                        input])

    # Format outputs: from nipype
    files = []
    bvecs = []
    bvals = []
    bids = []
    skip = False
    find_b = False
    for line in dcm2niiprocess.stdout.split("\n"):
        if not skip:
            out_file = None
            if line.startswith("Convert "):
                fname = str(re.search("\S+/\S+", line).group(0))
                output_dir = o
                out_file = os.path.abspath(os.path.join(output_dir, fname))
                # Extract bvals
                if find_b:
                    bvecs.append(out_file + ".bvec")
                    bvals.append(out_file + ".bval")
                    find_b = False
            # Next scan will have bvals/bvecs
            elif "DTI gradients" in line or "DTI gradient directions" in line:
                find_b = True
            else:
                pass
            if out_file:
                files.append(out_file + ".nii.gz")
                if b:
                    bids.append(out_file + ".json")
                continue
        skip = False

    return files, bvecs, bvals, bids


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


def nii2dcm(nii_file, outdir, sid=None, study_id=None, debug=False):
    """ Write a DICOM series from a Nifti array and create appropriate
    meta-data so it can be read by DICOM viewers.

    Writing the 3D image as a DICOM series is done by configuring the
    meta-data dictionary for each of the slices and then writing it in
    DICOM format. In our case we generate all of the meta-data to
    indicate that this series is derived. Note that we write the intensity
    values as is and thus do not set the rescale slope (0028|1053), rescale
    intercept (0028|1052) meta-data dictionary values.

    Parameters
    ----------
    nii_file: str
        The nifti image to convert.
    outdir: str
        The destination folder.
    sid: str, default None
        The subject identifier.
    study_id: str, default None
        The study name.
    debug: bool, default False
        If set try to reload the DICOM serie.

    Returns
    -------
    series_fnames: list of str
        The generated DICOM files.
    """
    import SimpleITK as sitk

    # Read the Nifti image
    img = sitk.ReadImage(nii_file)

    # DICOM does not support directly floating point value. The
    # only thing we can do is apply a well designed linear operation to
    # transform the floating point data to discretized one, here a simple
    # cast.
    print("Casting {0} to 32-bit unsigned integer.".format(
        img.GetPixelIDTypeAsString()))
    img = sitk.Cast(img, sitk.sitkUInt32)

    # Write the 3D image as a serie
    # IMPORTANT:
    # There are many DICOM tags that need to be updated when you modify an
    # original image. This is a delicate opration and requires knowlege of
    # the DICOM standard. This example only modifies some. For a more complete
    # list of tags that need to be modified see:
    #   http://gdcm.sourceforge.net/wiki/index.php/Writing_DICOM
    # If it is critical for your work to generate valid DICOM files,
    # It is recommended to use David Clunie's Dicom3tools to validate the files
    #   (http://www.dclunie.com/dicom3tools.html).
    writer = sitk.ImageFileWriter()

    # Use the study/series/frame of reference information given in the
    # meta-data dictionary and not the automatically generated information
    # from the file IO
    writer.KeepOriginalImageUIDOn()

    # Copy some of the tags and add the relevant tags indicating the change.
    # For the series instance UID (0020|000e), each of the components is a
    # number, cannot start with zero, and separated by a '.' We create a
    # unique series ID using the date and time.
    # Tags of interest:
    modification_time = time.strftime("%H%M%S")
    modification_date = time.strftime("%Y%m%d")
    direction = img.GetDirection()
    series_tag_values = [
        ("0008|0031", modification_time),  # Series Time
        ("0008|0021", modification_date),  # Series Date
        ("0008|0030", modification_time),  # Study Time
        ("0008|0020", modification_date),  # Study Date
        ("0008|0008", "DERIVED\\SECONDARY"),  # Image Type
        ("0010|0020", sid or "NA"),  # Patient ID
        ("0020|0010", study_id or "Convert " + modification_date),  # Study UID
        ("0020|000e", ("1.2.826.0.1.3680043.2.1125." + modification_date +
                       ".1" + modification_time)),  # Series Instance UID
        ("0020|000d", ("1.2.826.0.1.3680043.2.1125." + modification_date +
                       ".1" + modification_time)),  # Study Instance UID
        ("0020|0037", "\\".join(  # Image Orientation (Patient)
            map(str, (direction[0], direction[3], direction[6],
                      direction[1], direction[4], direction[7])))),
        ("0008|103e", "Created-NeuroSpin-SimpleITK")]  # Series Description

    # Write slices to output directory
    list(map(
        lambda index:
            write_slices(series_tag_values, img, index, outdir, writer),
            range(img.GetDepth())))

    # Re-read the series
    # Read the original series. First obtain the series file names using the
    # image series reader.
    series_ids = sitk.ImageSeriesReader.GetGDCMSeriesIDs(outdir)
    if not series_ids:
        raise ValueError("No DICOM files in '{0}'.".format(outdir))
    series_fnames = sitk.ImageSeriesReader.GetGDCMSeriesFileNames(
        outdir, series_ids[0])
    series_reader = sitk.ImageSeriesReader()
    series_reader.SetFileNames(series_fnames)

    if debug:
        # Configure the reader to load all of the DICOM tags (public+private):
        # By default tags are not loaded (saves time).
        # By default if tags are loaded, the private tags are not loaded.
        # We explicitly configure the reader to load tags, including the
        # private ones.
        series_reader.LoadPrivateTagsOn()
        new_img = series_reader.Execute()
        print(new_img.GetSpacing(), "vs", img.GetSpacing())

    return series_fnames


def write_slices(series_tag_values, img, index, outdir, writer):
    """ Write a DICOM slice.

    Parameters
    ----------
    """
    # Get the slice
    image_slice = img[:, :, index]

    # Tags shared by the series.
    list(map(lambda tag_value: image_slice.SetMetaData(
        tag_value[0], tag_value[1]), series_tag_values))

    # Slice specific tags.
    image_slice.SetMetaData(
        "0008|0012", time.strftime("%Y%m%d"))  # Instance Creation Date
    image_slice.SetMetaData(
        "0008|0013", time.strftime("%H%M%S"))  # Instance Creation Time

    # Setting the modality type to MR preserves the slice location.
    image_slice.SetMetaData("0008|0060", "MR")

    # (0020, 0032) image position patient determines the 3D spacing between
    # slices.
    image_slice.SetMetaData("0020|0032", "\\".join(map(
        str, img.TransformIndexToPhysicalPoint((0, 0, index)))))
    image_slice.SetMetaData("0020|0013", str(index))  # Instance Number

    # Write to the output directory and add the extension dcm, to force
    # writing in DICOM format.
    writer.SetFileName(os.path.join(outdir, str(index) + ".dcm"))
    writer.Execute(image_slice)
