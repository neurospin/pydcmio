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
import nibabel
import numpy
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
from pydcmio.dcmconverter.converter import dcm2nii
from pydcmio.dcmconverter.converter import add_meta_to_nii
from pydcmio.dcmreader.reader import STANDARD_EXTRACTOR


class PyDcmioDcm2Nii(unittest.TestCase):
    """ Test the PyDcmio dicom to nifti conversion:
    'pydcmio.dcmconverter.converter.dcm2nii'
    """
    def setUp(self):
        """ Run before each test - the mock_popen will be available and in the
        right state in every test<something> function.
        """
        # Mocking popen
        self.popen_patcher = patch("pydcmio.dcm2nii.wrapper.subprocess.Popen")
        self.mock_popen = self.popen_patcher.start()
        mock_process = mock.Mock()
        stdout = [
            "Saving /my/path/mock_convertedfile",
            "GZip...mock_convertedgzfile",
            "Number of diffusion directions X",
            "Cropping NIfTI/Analyze image /my/path/mock_rconvertedfile"
        ]
        attrs = {
            "communicate.return_value": ("\n".join(stdout),
                                         "mock_NONE"),
            "returncode": 0
        }
        mock_process.configure_mock(**attrs)
        self.mock_popen.return_value = mock_process

        # Define function parameters
        self.kwargs = {
            "input": "/my/path/mock_infile",
            "o": "/my/path/mock_outdir",
            "b": "/my/path/mock_configfile"
        }

    def tearDown(self):
        """ Run after each test.
        """
        self.popen_patcher.stop()

    @mock.patch("pydcmio.dcmconverter.converter.os.path.isfile")
    def test_badfileerror_raise(self, mock_isfile):
        """ Bad input file -> raise ValueError.
        """
        # Set the mocked functions returned values
        mock_isfile.side_effect = [False, ]

        # Test execution
        self.assertRaises(ValueError, dcm2nii, **self.kwargs)

    @mock.patch("{0}.open".format(mock_builtin))
    @mock.patch("pydcmio.dcmconverter.converter.os.path.isfile")
    def test_nooutdir_raise(self, mock_isfile, mock_open):
        """ No 'OutDir' in config -> raise ValueError.
        """
        # Set the mocked functions returned values
        mock_isfile.side_effect = [True, ]
        mock_context_manager = mock.Mock()
        mock_open.return_value = mock_context_manager
        mock_file = mock.Mock()
        mock_file.readlines.return_value = ["WRONG"]
        mock_enter = mock.Mock()
        mock_enter.return_value = mock_file
        mock_exit = mock.Mock()
        setattr(mock_context_manager, "__enter__", mock_enter)
        setattr(mock_context_manager, "__exit__", mock_exit)

        # Test execution
        self.assertRaises(ValueError, dcm2nii, **self.kwargs)

    @mock.patch("{0}.open".format(mock_builtin))
    @mock.patch("pydcmio.dcmconverter.converter.os.path.isfile")
    def test_normal_execution(self, mock_isfile, mock_open):
        """ Test the normal behaviour of the function.
        """
        # Set the mocked functions returned values
        mock_isfile.side_effect = [True, ]
        mock_context_manager = mock.Mock()
        mock_open.return_value = mock_context_manager
        mock_file = mock.Mock()
        mock_file.readlines.return_value = ["OutDir=/my/path/mock_outdir"]
        mock_enter = mock.Mock()
        mock_enter.return_value = mock_file
        mock_exit = mock.Mock()
        setattr(mock_context_manager, "__enter__", mock_enter)
        setattr(mock_context_manager, "__exit__", mock_exit)

        # Test execution
        (files, reoriented_files, reoriented_and_cropped_files, bvecs,
         bvals) = dcm2nii(**self.kwargs)
        self.assertEqual(files,
                         ["/my/path/mock_convertedfile",
                          "/my/path/mock_outdir/mock_convertedgzfile"])
        self.assertEqual(reoriented_files, [])
        self.assertEqual(reoriented_and_cropped_files,
                         ["/my/path/cmock_rconvertedfile"])
        self.assertEqual(bvecs,
                         ["/my/path/mock_outdir/mock_convertedgzfile.bvec"])
        self.assertEqual(bvals,
                         ["/my/path/mock_outdir/mock_convertedgzfile.bval"])


class PyDcmioAddMeta(unittest.TestCase):
    """ Test the PyDcmio add metadata to nifti:
    'pydcmio.dcmconverter.converter.add_meta_to_nii'
    """
    def setUp(self):
        """ Define function parameters
        """
        test_dir = resource_filename(Requirement.parse("pydicom"),
                                     "dicom/testfiles")
        self.basename = "MR_small.dcm"
        self.dataset_or_dcmpath = os.path.join(test_dir, self.basename)
        self.kwargs = {
            "nii_file": "/my/path/mock_niifile",
            "dicom_dir":  test_dir,
            "dcm_tags":  [("TE", STANDARD_EXTRACTOR["get_echo_time"][0],
                           False)],
            "outdir":  "/my/path/mock_outdir",
            "prefix": "f",
            "additional_information": None
        }

    @mock.patch("pydcmio.dcmconverter.converter.nibabel.load")
    @mock.patch("pydcmio.dcmconverter.converter.os.listdir")
    @mock.patch("pydcmio.dcmconverter.converter.os.path.isdir")
    def test_badimagetype_raise(self, mock_isdir, mock_listdir, mock_load):
        """ Bad input dicom directory -> raise ValueError.
        """
        # Set the mocked functions returned values
        mock_isdir.side_effect = [True, ]
        mock_listdir.return_value = [self.basename]
        mock_load.return_value = None

        # Test execution
        self.assertRaises(ValueError, add_meta_to_nii, **self.kwargs)

    @mock.patch("pydcmio.dcmconverter.converter.nibabel.save")
    @mock.patch("pydcmio.dcmconverter.converter.nibabel.load")
    @mock.patch("pydcmio.dcmconverter.converter.os.listdir")
    @mock.patch("pydcmio.dcmconverter.converter.os.path.isdir")
    def test_normal_execution(self, mock_isdir, mock_listdir, mock_load,
                              mock_save):
        """ Test the normal behaviour of the function."""
        # Set the mocked functions returned values
        mock_isdir.side_effect = [True, ]
        mock_listdir.return_value = [self.basename]
        mock_load.return_value = nibabel.Nifti1Image(numpy.zeros((10, 10)),
                                                     numpy.eye(4))

        # Test execution
        filled_nii_file = add_meta_to_nii(**self.kwargs)
        self.assertEqual(
            os.path.join(self.kwargs["outdir"], self.kwargs["prefix"] +
                         os.path.basename(self.kwargs["nii_file"])),
            filled_nii_file)
        self.assertEqual([mock.call(mock_load.return_value, filled_nii_file)],
                         mock_save.call_args_list)


if __name__ == "__main__":
    unittest.main()
