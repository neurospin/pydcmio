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

# Pydcmio import
from pydcmio.dcmreader.reader import walk
from pydcmio.dcmreader.reader import get_values
from pydcmio.dcmreader.reader import STANDARD_EXTRACTOR
from pkg_resources import Requirement, resource_filename


class PyDcmioReader(unittest.TestCase):
    """ Test the PyDcmio dicom reader functions:
    'pydcmio.dcmreader.reader.walk' and 'pydcmio.dcmreader.reader.get_values'
    """
    def setUp(self):
        """ Run before each test - the mock_popen will be available and in the
        right state in every test<something> function.
        """
        # Define function parameters
        test_dir = resource_filename(Requirement.parse("pydicom"),
                                     "dicom/testfiles")
        self.dataset_or_dcmpath = os.path.join(test_dir, "MR_small.dcm")

    def test_badextractor_raise(self):
        """ Bad extractor -> raise ValueError.
        """
        # Test execution
        self.assertRaises(ValueError, get_values, self.dataset_or_dcmpath,
                          "WRONG")

    def test_badfileerror_raise(self):
        """ Bad input file -> raise ValueError.
        """
        # Test execution
        self.assertRaises(ValueError, walk, "WRONG", None, stack_values=False)

    def test_baddataset_raise(self):
        """ Bad dataset -> raise ValueError.
        """
        # Test execution
        self.assertRaises(ValueError, walk, object, None, stack_values=False)

    def test_normal_execution(self):
        """ Test the normal behaviour of the function.
        """
        # Test execution
        value = get_values(self.dataset_or_dcmpath, "get_echo_time")
        self.assertEqual(value, 240.)
        tag = STANDARD_EXTRACTOR["get_echo_time"][0]
        values = walk(self.dataset_or_dcmpath, tag, stack_values=False)
        self.assertEqual(values, [240.])
        values = walk(self.dataset_or_dcmpath, tag, stack_values=True)
        self.assertEqual(values, [240.])


if __name__ == "__main__":
    unittest.main()
