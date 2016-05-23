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
else:
    import unittest.mock as mock
    from unittest.mock import patch

# Pydcmio import
from pydcmio.dcmconverter.spliter import split_series


class PyDcmioSplit(unittest.TestCase):
    """ Test the PyDcmio dicom files spliter function:
    'pydcmio.dcmconverter.spliter.split_series'
    """
    def setUp(self):
        """ Define function parameters
        """
        test_dir = resource_filename(Requirement.parse("pydicom"),
                                     "dicom/testfiles")
        self.dataset_or_dcmpath = os.path.join(test_dir, "MR_small.dcm")
        self.kwargs = {
            "dicom_dir": test_dir,
            "outdir":  "/my/path/mock_outdir"
        }

    @mock.patch("pydcmio.dcmconverter.spliter.shutil.copy2")
    @mock.patch("pydcmio.dcmconverter.spliter.os.mkdir")
    @mock.patch("pydcmio.dcmconverter.spliter.os.walk")
    def test_normal_execution(self, mock_walk, mock_mkdir, mock_copy):
        """ Test the normal behaviour of the function."""
        # Set the mocked functions returned values
        mock_walk.return_value = [
            (os.path.dirname(self.dataset_or_dcmpath), (),
             (os.path.basename(self.dataset_or_dcmpath), ))
        ]

        # Test execution
        split_series(**self.kwargs)
        self.assertEqual([
            mock.call(self.dataset_or_dcmpath, os.path.join(
                self.kwargs["outdir"], "240.0000_000001",
                "1.3.6.1.4.1.5962.1.1.4.1.1.20040826185059.5457.dcm"))],
            mock_copy.call_args_list)
        self.assertEqual([
            mock.call(os.path.join(
                self.kwargs["outdir"], "240.0000_000001"))],
            mock_mkdir.call_args_list)


if __name__ == "__main__":
    unittest.main()
