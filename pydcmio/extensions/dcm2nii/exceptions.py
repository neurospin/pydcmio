##########################################################################
# NSAp - Copyright (C) CEA, 2013 - 2016
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################


class Dcm2NiiError(Exception):
    """ Base exception type for the package.
    """
    def __init__(self, message):
        super(Dcm2NiiError, self).__init__(message)


class Dcm2NiiRuntimeError(Dcm2NiiError):
    """ Error thrown when call to the Dcm2Nii software failed.
    """
    def __init__(self, algorithm_name, parameters, error=None):
        message = (
            "Dcm2Nii call for '{0}' failed, with parameters: '{1}'. Error:: "
            "{2}.".format(algorithm_name, parameters, error))
        super(Dcm2NiiRuntimeError, self).__init__(message)


class Dcm2NiiConfigurationError(Dcm2NiiError):
    """ Error thrown when call to the Dcm2Nii software failed.
    """
    def __init__(self, command_name):
        message = "Dcm2Nii command '{0}' not found.".format(command_name)
        super(Dcm2NiiConfigurationError, self).__init__(message)


class Dcm2NiiResultError(Dcm2NiiError):
    """ Error thrown when the Dcm2Nii software has returned a strange result.
    """
    def __init__(self, command):
        message = ("Dcm2Nii command '{0}' may have returned a strange "
                   "result.".format(command))
        super(FSLResultError, self).__init__(message)
