##########################################################################
# NSAP - Copyright (C) CEA, 2015
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################


# System import
from __future__ import print_function
import unittest


def pilot_dcmanon():
    """
    Imports
    -------

    This code needs 'capsul' and 'mmutils' packages in order to instanciate and
    execute the pipeline and to get a toy dataset.
    These packages are available in the 'neurospin' source list or in pypi.
    It also requires the 'pydicom' package in order to be able to read the
    DICOM fields.
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
    description that will perform the DICOMs anonimization, and the 'outdir'
    the location of the pipeline's results: in this case a temporary directory.
    """
    pipeline_name = "dcmio.dcmanonymizer.dcm_anonymizer.xml"
    outdir = tempfile.mkdtemp()

    """
    Capsul configuration
    --------------------

    A 'StudyConfig' has to be instantiated in order to execute the pipeline
    properly. It enables us to define the results directory through the
    'output_directory' attribute, the number of CPUs to be used through the
    'number_of_cpus' attributes, and to specify that we want a log of the
    processing step through the 'generate_logging'. The 'use_scheduler'
    must be set to True if more than 1 CPU are used.
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
    parametrized: we only need to set the path to the DICOM folder to be
    anonymized. Note that this folder is expected to contain only DICOM files.
    """
    pipeline = get_process_instance(pipeline_name)
    pipeline.dcmdirs = [dcmfolder, dcmfolder]

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

    The 'pydicom' package is used to load the generated DICOMs. We display the
    patient name to check the anonimization process.
    """
    import dicom

    for rundcmfile in pipeline.dcmfiles:
        dcmfile = rundcmfile[0]
        dataset = dicom.read_file(dcmfile, force=True)
        print(dataset[(0x0010, 0x0010)])
        if dataset[(0x0010, 0x0010)].value != "John Doe":
            raise Exception("Dataset has not been de-idetnify properly.")


class TestDcmAnon(unittest.TestCase):
    """ Class to test dicom anonymization pipeline.
    """
    def test_dcm_anon(self):
        """ Method to test a simple 1 cpu call with the scheduler.
        """
        pilot_dcmanon()


def test():
    """ Function to execute unitest
    """
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDcmAnon)
    runtime = unittest.TextTestRunner(verbosity=2).run(suite)
    return runtime.wasSuccessful()


if __name__ == "__main__":
    test()
