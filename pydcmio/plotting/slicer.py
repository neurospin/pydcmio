##########################################################################
# NSAp - Copyright (C) CEA, 2013 - 2016
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
import numpy
import nibabel
import os

# QAP import
from qap.viz.plotting import plot_mosaic


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
    title (optional, default None)
        the mosaic title.

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
        raise ValueError("'{0}' is not a 3d or 4d image.".format(impath))
    if array.ndim == 4 and strategy == "average":
        array = numpy.mean(array, axis=3)
    if array.ndim == 4 and strategy == "pick":
        try:
            array = numpy.mean(array[..., indices], axis=3)
        except:
            raise ValueError("Can't pick volume indices '{0}' in array of "
                             "shape '{1}'.".format(indices, array.shape))

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
