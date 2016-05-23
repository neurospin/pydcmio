#! /usr/bin/env python
##########################################################################
# NSAP - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
import os
import subprocess

# Dcmio import
from .exceptions import Dcm2NiiConfigurationError
from .exceptions import Dcm2NiiRuntimeError

MAP = {
    True: "y",
    False: "n"
}


class Dcm2NiiWrapper(object):
    """ Parent class for the wrapping of Dcm2Nii functions.
    """

    def __init__(self, name):
        """ Initialize the Dcm2NiiWrapper class by setting properly the
        environment.

        Parameters
        ----------
        name: str (mandatory)
            the name of the Dcm2Nii binary to be called.
        """
        self.name = name
        self.cmd = None
        self.environment = os.environ
        self.version = Dcm2NiiWrapper.version(self.name)

    def __call__(self, cmd):
        """ Run the Dcm2Nii command.

        Note that the command is built from the parent frame.
        """
        # Update the command to execute
        self.cmd = cmd

        # Check Dcm2Nii has been configured so the command can be found
        process = subprocess.Popen(
            ["which", self.cmd[0]],
            env=self.environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        self.stdout, self.stderr = process.communicate()
        self.exitcode = process.returncode
        if self.exitcode != 0:
            raise Dcm2NiiConfigurationError(self.cmd[0])

        # Execute the command
        process = subprocess.Popen(
            self.cmd,
            env=self.environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        self.stdout, self.stderr = process.communicate()
        self.exitcode = process.returncode

        # Check if the command return a valid exit code
        if self.exitcode != 0:
            raise Dcm2NiiRuntimeError(self.cmd[0], " ".join(self.cmd[1:]),
                                      self.stderr)

    @classmethod
    def version(cls, name):
        """ Get the version of the command.

        Parameters
        ----------
        name: str (mandatory)
            the name of the Dcm2Nii binary to be called.
        """
        # Execute the help command
        process = subprocess.Popen(
            [name],
            env=os.environ,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        exitcode = process.returncode

        # Check if the command return a valid exit code
        if exitcode != 0:
            raise Dcm2NiiRuntimeError(name, "--version", stderr)

        return stdout.splitlines()[0]
