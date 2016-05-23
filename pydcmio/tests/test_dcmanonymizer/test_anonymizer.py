##########################################################################
# NSAp - Copyright (C) CEA, 2016
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
import unittest
import sys
import os
from pkg_resources import Requirement, resource_filename
# COMPATIBILITY: since python 3.3 mock is included in unittest module
python_version = sys.version_info
if python_version[:2] <= (3, 3):
    import mock
    from mock import patch
    mock_builtin = "__builtin__"
else:
    import unittest.mock as mock
    from unittest.mock import patch
    mock_builtin = "builtins"

# Pydcmio import
from pydcmio.dcmanonymizer.anonymize import anonymize_dicomdir


class PyDcmioAnon(unittest.TestCase):
    """ Test the PyDcmio dicom files anonimizer function:
    'pydcmio.dcmanonymizer.anonymize.anonymize_dicomdir'
    """
    def setUp(self):
        """ Define function parameters
        """
        test_dir = resource_filename(Requirement.parse("pydicom"),
                                     "dicom/testfiles")
        self.dataset_or_dcmpath = os.path.join(test_dir, "MR_small.dcm")
        self.kwargs = {
            "inputdir": test_dir,
            "outdir":  "/my/path/mock_outdir",
            "write_logs": False
        }

    @mock.patch("pydcmio.dcmanonymizer.anonymize.dicom.dataset.Dataset."
                "save_as")
    @mock.patch("pydcmio.dcmanonymizer.anonymize.os.listdir")
    def test_normal_execution(self, mock_listdir, mock_saveas):
        """ Test the normal behaviour of the function."""
        # Set the mocked functions returned values
        mock_listdir.return_value = [os.path.basename(self.dataset_or_dcmpath)]

        # Test execution
        dcmfiles, logfiles = anonymize_dicomdir(**self.kwargs)
        expected_dcmfiles = [
            os.path.join(self.kwargs["outdir"], "0.dcm")
        ]
        self.assertEqual(expected_dcmfiles, dcmfiles)
        self.assertEqual([None], logfiles)
        self.assertEqual([mock.call(expected_dcmfiles[0])],
                         mock_saveas.call_args_list)


if __name__ == "__main__":
    unittest.main()
