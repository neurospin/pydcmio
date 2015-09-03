#! /usr/bin/env python
##########################################################################
# NSAp - Copyright (C) CEA, 2015
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
import unittest


def pilot_dcm2nii():
    """ 
    Dicom to nifti.

    Imports
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
    """
    pipeline_name = "dcmio.dcmconverter.dcm_to_nii.xml"
    outdir = tempfile.mkdtemp()

    """
    Configure the environment
    """
    study_config = StudyConfig(
        modules=[],
        use_smart_caching=True,
        output_directory=self.outdir,
        number_of_cpus=1,
        generate_logging=True,
        use_scheduler=True)

    """
    Create pipeline
    """
    pipeline = get_process_instance(self.pipeline_name)
    pipeline.date_in_filename = True

    """
    Set pipeline input parameters
    """
    dicom_dataset = get_sample_data("dicom")
    dcmfolder = os.path.join(self.outdir, "dicom")
    if not os.path.isdir(dcmfolder):
        os.makedirs(dcmfolder)
    shutil.copy(dicom_dataset.barre, os.path.join(dcmfolder, "heart.dcm"))
    pipeline.source_dir = dcmfolder

    """
    View pipeline
    """
    if 0:
        from capsul.qt_gui.widgets import PipelineDevelopperView
        from PySide import QtGui
        app = QtGui.QApplication(sys.argv)
        view1 = PipelineDevelopperView(pipeline)
        view1.show()
        app.exec_()

    """
    Execute the pipeline in the configured study
    """
    study_config.run(pipeline)


class TestDcmToNii(unittest.TestCase):
    """ Class to test dicom to nifti pipeline.
    """
    def test_simple_run(self):
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
