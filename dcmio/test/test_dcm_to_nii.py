#! /usr/bin/env python
##########################################################################
# NSAp - Copyright (C) CEA, 2015
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
from __future__ import print_function
import unittest


def pilot_dcm2nii():
    """
    Imports
    -------

    This code needs 'capsul' and 'mmutils' package in order to instanciate and
    execute the pipeline and to get a toy dataset.
    These packages are available in the 'neurospin' source list or in pypi.
    """
    import os
    import sys
    import shutil
    import tempfile
    from capsul.study_config.study_config import StudyConfig
    from capsul.process.loader import get_process_instance
    from mmutils.toy_datasets import get_sample_data

    """
    Parameters
    ----------

    The 'pipeline_name' parameter contains the location of the pipeline XML
    description that will perform the DICOMs conversion, and the 'outdir' the
    location of the pipeline's results: in this case a temporary directory.
    """
    pipeline_name = "dcmio.dcmconverter.dcm_to_nii.xml"
    outdir = tempfile.mkdtemp()

    """
    Capsul configuration
    --------------------

    A 'StudyConfig' has to be instantiated in order to execute the pipeline
    properly. It enables us to define the results directory through the
    'output_directory' attribute, the number of CPUs to be used through the
    'number_of_cpus' attributes, and to specify that we want a log of the
    processing step through the 'generate_logging'. The 'use_scheduler'
    must be set to True if more than 1 CPU is used.
    """
    study_config = StudyConfig(
        modules=[],
        output_directory=outdir,
        number_of_cpus=1,
        generate_logging=True,
        use_scheduler=True)

    """
    Get the toy dataset
    -------------------

    The toy dataset is composed of a 3D heart dicom image that is downloaded
    if it is necessary throught the 'get_sample_data' function and exported
    locally in a 'heart.dcm' file.
    """
    dicom_dataset = get_sample_data("dicom")
    dcmfolder = os.path.join(outdir, "dicom")
    if not os.path.isdir(dcmfolder):
        os.makedirs(dcmfolder)
    shutil.copy(dicom_dataset.barre, os.path.join(dcmfolder, "heart.dcm"))

    """
    Pipeline definition
    -------------------

    The pipeline XML description is first imported throught the
    'get_process_instance' method, and the resulting pipeline instance is
    parametrized: in this example we decided to set the date in the converted
    file name and we set two DICOM directories to be converted in Nifti
    format.
    """
    pipeline = get_process_instance(pipeline_name)
    pipeline.date_in_filename = True
    pipeline.dicom_directories = [dcmfolder, dcmfolder]
    pipeline.additional_informations = [[("Provided by", "Neurospin@2015")],
                                        [("Provided by", "Neurospin@2015"),
                                         ("TR", "1500")]]
    pipeline.dcm_tags = [("TR", ("0x0018", "0x0080")),
                         ("TE", ("0x0018", "0x0081"))]

    """
    Pipeline representation
    -----------------------

    By executing this block of code, a pipeline representation can be
    displayed. This representation is composed of boxes connected to each
    other.
    """
    if 0:
        from capsul.qt_gui.widgets import PipelineDevelopperView
        from PySide import QtGui
        app = QtGui.QApplication(sys.argv)
        view1 = PipelineDevelopperView(pipeline)
        view1.show()
        app.exec_()

    """
    Pipeline execution
    ------------------

    Finally the pipeline is eecuted in the defined 'study_config'.
    """
    study_config.run(pipeline)

    """
    Access the result
    -----------------

    The 'nibabel' package is used to load the generated images. We display the
    numpy array shape and the stored repetiton and echo times: in order
    to load the 'descrip' image field we use the 'json' package.
    """
    import json
    import copy
    import nibabel

    generated_images = pipeline.filled_converted_files

    for fnames in generated_images:
        print(">>>", fnames, "...")
        im = nibabel.load(fnames[0])
        print("shape=", im.get_data().shape)
        header = im.get_header()
        a = str(header["descrip"])
        a = a.strip()
        description = json.loads(copy.deepcopy(a))
        print("TE=", description["TE"])
        print("TR=", description["TR"])
        print("Provided by=", description["Provided by"])


class TestDcmToNii(unittest.TestCase):
    """ Class to test dicom to nifti pipeline.
    """
    def test_dcm_to_nii(self):
        """ Method to test a simple 1 cpu call with the scheduler.
        """
        pilot_dcm2nii()


def test():
    """ Function to execute unitest
    """
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDcmToNii)
    runtime = unittest.TextTestRunner(verbosity=2).run(suite)
    return runtime.wasSuccessful()


if __name__ == "__main__":
    test()
