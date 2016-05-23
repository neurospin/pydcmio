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
import math
import time
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import FigureCanvasPdf as FigureCanvas


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


def plot_mosaic(nifti_file, title=None, overlay_mask=None,
                figsize=(11.7, 8.3)):
    """ From the qap module.
    """
    from pylab import cm

    if isinstance(nifti_file, str):
        nii = nibabel.load(nifti_file)
        mean_data = nii.get_data()
    else:
        mean_data = nifti_file

    z_vals = np.array(range(0, mean_data.shape[2]))
    # Reduce the number of slices shown
    if mean_data.shape[2] > 70:
        rem = 15
        # Crop inferior and posterior
        mean_data = mean_data[..., rem:-rem]
        z_vals = z_vals[rem:-rem]
        # Discard one every two slices
        mean_data = mean_data[..., ::2]
        z_vals = z_vals[::2]

    n_images = mean_data.shape[2]
    row, col = _calc_rows_columns(figsize[0] / figsize[1], n_images)

    if overlay_mask:
        overlay_data = nibabel.load(overlay_mask).get_data()

    # create figures
    fig = plt.Figure(figsize=figsize)
    FigureCanvas(fig)

    fig.subplots_adjust(top=0.85)
    for image, z_val in enumerate(z_vals):
        ax = fig.add_subplot(row, col, image + 1)
        data_mask = np.logical_not(np.isnan(mean_data))
        if overlay_mask:
            ax.set_rasterized(True)

        ax.imshow(np.fliplr(mean_data[:, :, image].T), vmin=np.percentile(
            mean_data[data_mask], 0.5),
            vmax=np.percentile(mean_data[data_mask], 99.5),
            cmap=cm.Greys_r, interpolation='nearest', origin='lower')

        if overlay_mask:
            cmap = cm.Reds  # @UndefinedVariable
            cmap._init()
            alphas = np.linspace(0, 0.75, cmap.N + 3)
            cmap._lut[:, -1] = alphas
            ax.imshow(np.fliplr(overlay_data[:, :, image].T), vmin=0, vmax=1,
                      cmap=cmap, interpolation='nearest', origin='lower')

        ax.annotate(
            str(z_val), xy=(.95, .015), xycoords='axes fraction',
            fontsize=10, color='white', horizontalalignment='right',
            verticalalignment='bottom')

        ax.axis('off')

    fig.subplots_adjust(
        left=0.05, right=0.95, bottom=0.05, top=0.95, wspace=0.01, hspace=0.1)

    if not title:
        _, title = os.path.split(nifti_file)
        title += " (last modified: %s)" % time.ctime(
            os.path.getmtime(nifti_file))
    fig.suptitle(title, fontsize='10')
    return fig


def _calc_rows_columns(ratio, n_images):
    """ From the qap module.
    """
    rows = 1
    for _ in range(100):
        columns = math.floor(ratio * rows)
        total = rows * columns
        if total > n_images:
            break

        columns = math.ceil(ratio * rows)
        total = rows * columns
        if total > n_images:
            break
        rows += 1
    return rows, columns
