##########################################################################
# NSAp - Copyright (C) CEA, 2013 - 2018
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

"""
Diverse RTstruct Dicom reading functions to extract precise information.
"""

# System import
from __future__ import print_function
import dicom
import os
from pprint import pprint

# Third party import
import numpy as np
import nibabel
from pyfreesurfer.utils.surftools import apply_affine_on_mesh
from pyconnectome.utils.reorient import swap_affine


def regions_of_interest(rtstruct_file):
    """ Return list of all structure names.

    Parameters
    ----------
    rtstruct_file: str
        the RTstruct Dicom files.

    Returns
    -------
    rois: dict
        the ROI information: name, number of point, number of slices.
    """
    rois = {}
    dataset = dicom.read_file(rtstruct_file)
    rois_struct = dataset.StructureSetROISequence
    names = [rois_struct[idx].ROIName for idx in range(len(rois_struct))]
    for cnt, name in enumerate(names):
        slices = dataset.ROIContours[cnt].Contours
        num_slices = len(slices)
        if slices[0].ContourGeometricType == "CLOSED_PLANAR":
            num_pts = [slices[idx].NumberOfContourPoints
                       for idx in range(num_slices)]
            num_pts = np.array(num_pts).astype(int)
            num_pts = np.sum(num_pts)
            rois.update({
                name: {
                    "num_slices": num_slices,
                    "num_pts": num_pts}
            })
    return rois


def points_of_interest(rtstruct_file):
    """ Find POIs return as dict and display names and coordinates.

    Parameters
    ----------
    rtstruct_file: str
        the RTstruct dicom files.


    Returns
    -------
    rois: dict
        the ROI information: name, points in physical space, method.
    sop_instance_uids: list of str
        the associated volume slice SOp instance UIDs.
    institution: str
        the name of the institution in charge of the segmentation.
    operator: str
        the name of the person in charge of the segmentation.
    """
    rois = {}
    dataset = dicom.read_file(rtstruct_file)
    operator = dataset.OperatorsName
    institution = dataset.InstitutionName
    rois_struct = dataset.StructureSetROISequence
    names = [rois_struct[idx].ROIName for idx in range(len(rois_struct))]
    for cnt, name in enumerate(names):
        cntr = dataset.ROIContours[cnt].Contours[0]
        method = rois_struct[cnt].ROIGenerationAlgorithm
        num_pts = cntr.NumberOfContourPoints
        if cntr.ContourGeometricType == "CLOSED_PLANAR":
            try:
                frames = []
                for cntr_seq in cntr.ContourImageSequence:
                    frames.append(int(cntr_seq.RefdFrameNumber))
            except:
                frames = None
            pt_loc = np.asarray([float(xyz) for xyz in cntr.ContourData])
            pt_loc = pt_loc.reshape(-1, 3)
            rois.update({
                name: (pt_loc.tolist(), method, frames)
            })
    sop_instance_uids = []
    for slice_struct in (dataset.ReferencedFrameOfReferenceSequence[0].
                         RTReferencedStudySequence[0].
                         RTReferencedSeriesSequence[0].ContourImageSequence):
        sop_instance_uids.append(slice_struct.ReferencedSOPInstanceUID)
    return rois, sop_instance_uids, institution, operator


def generate_masks(rois, ref_file, outdir, axes="RAS", fname="mask"):
    """ Genrate Nifti masks from RTstruct data.

    Parameters
    ----------
    rois: dict
        the ROI information: name, points in physical space, method.
    ref_file: str
        the Nifti mask reference file.
    outdir: str
        the destination folder
    axes: str, default 'RAS'
        the ROIs points orientation axes.
    fname: str, default 'mask'
        the name of the generated mask file.

    Returns
    -------
    mask_file: str
        the generated masks from the RTstruct: a 4D volume.
    """
    ref_im = nibabel.load(ref_file)
    ref_data = ref_im.get_data()
    shape = ref_data.shape
    reorient_aff = swap_affine(axes)
    affine = np.dot(reorient_aff, ref_im.affine)
    inv_aff = np.linalg.inv(affine)
    mask = None
    for name, (pt_loc, method, frames) in rois.items():
        cmask = np.zeros(shape + (1, ), dtype=int)
        pt_loc = np.asarray(pt_loc)
        pt_loc_vox = np.round(apply_affine_on_mesh(
            pt_loc, inv_aff)).astype(int)
        for pt in pt_loc_vox:
            cmask[tuple(pt)] = 1
        if mask is None:
            mask = cmask
        else:
            mask = np.concatenate((mask, cmask), axis=-1)
    mask_im = nibabel.Nifti1Image(mask, ref_im.affine)
    mask_file = os.path.join(outdir, "{0}.nii.gz".format(fname))
    nibabel.save(mask_im, mask_file)
    return mask_file
