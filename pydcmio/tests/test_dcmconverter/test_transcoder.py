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
import copy
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
from pydcmio.dcmconverter.transcoder import transcode_sids


class PyDcmioTranscode(unittest.TestCase):
    """ Test the PyDcmio subject identifier transcodage function:
    'pydcmio.dcmconverter.transcoder.transcode_sids'
    """
    def setUp(self):
        """ Define function parameters
        """
        self.kwargs = {
            "sids": ["Subject1", "Subject2"],
            "transcoding_table":  "/my/path/mock_tablefile"
        }

    @mock.patch("pydcmio.dcmconverter.converter.os.path.isfile")
    def test_badfileerror_raise(self, mock_isfile):
        """ Bad input file -> raise ValueError.
        """
        # Set the mocked functions returned values
        mock_isfile.side_effect = [False, ]

        # Test execution
        self.assertRaises(ValueError, transcode_sids, **self.kwargs)

    @mock.patch("pydcmio.dcmconverter.converter.json.dump")
    @mock.patch("pydcmio.dcmconverter.converter.json.load")
    @mock.patch("{0}.open".format(mock_builtin))
    @mock.patch("pydcmio.dcmconverter.converter.os.path.isfile")
    def test_normal_execution(self, mock_isfile, mock_open, mock_load,
                              mock_dump):
        """ Test the normal behaviour of the function."""
        # Set the mocked functions returned values
        mock_isfile.side_effect = [True, ]
        mock_context_manager = mock.Mock()
        mock_open.return_value = mock_context_manager
        mock_file = mock.Mock()
        mock_file.read.return_value = ["MOCK"]
        mock_enter = mock.Mock()
        mock_enter.return_value = mock_file
        mock_exit = mock.Mock()
        setattr(mock_context_manager, "__enter__", mock_enter)
        setattr(mock_context_manager, "__exit__", mock_exit)
        mock_load.return_value = {"Subject1": "007"}

        # Test execution
        transcode_sids(**self.kwargs)
        self.assertEqual(len(mock_dump.call_args_list), 1)
        transcoding = mock_dump.call_args_list[0][0][0]
        self.assertEqual(sorted(transcoding.keys()), self.kwargs["sids"])
        for sid in self.kwargs["sids"]:
            if sid in mock_load.return_value:
                self.assertEqual(mock_load.return_value[sid], transcoding[sid])
            else:
                self.assertTrue(isdigit(transcoding[sid]))


if __name__ == "__main__":
    unittest.main()
