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
import json
import inspect

# Dcmio import
from .exceptions import Dcm2NiiConfigurationError

MAP = {
    True: "y",
    False: "n"
}

class Dcm2NiiWrapper(object):
    """ Parent class for the wrapping of Dcm2Nii functions. 
    """  
 
    def __init__(self, name, optional=None):
        """ Initialize the Dcm2NiiWrapper class by setting properly the
        environment.
        
        Parameters
        ----------
        name: str (mandatory)
            the name of the Dcm2Nii binary to be called.
        optional: list (optional, default None)
            the name of the optional parameters. If 'ALL' consider that all
            the parameter are optional.
        """
        self.name = name
        self.cmd = name.split()
        self.optional = optional or []
        self.environment = os.environ

    def __call__(self):
        """ Run the Dcm2Nii command.

        Note that the command is built from the parent frame.
        """
        # Update the command to execute
        self._update_command()

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

    def _update_command(self):
        """ Update the command that will be executed.
        """
        # Get the caller frame parameters
        caller_frame = inspect.stack()[2][0]
        args, _, _, values = inspect.getargvalues(caller_frame)

        # 'ALL' optional case
        if self.optional == 'ALL':
            self.optional = args

        # Update the command
        input_sources = []
        for parameter_name in args:
        
            # Get parameter value
            parameter_value = values[parameter_name]

            # Clean parameter name
            cmd_parameter_name = parameter_name
            if parameter_name.endswith("_file"):
                cmd_parameter_name = parameter_name.replace("_file", "")

            if parameter_value is not None:

                # Mandatory parameter
                if parameter_name in ["input"]:
                    input_sources.append(parameter_value)

                # Boolean parameter
                elif isinstance(parameter_value, bool):
                    if parameter_name in self.optional:
                        self.cmd.append("--{0}={1}".format(
                            cmd_parameter_name, MAP[parameter_value]))
                    else:
                        self.cmd.append("-{0}".format(cmd_parameter_name))
                        self.cmd.append("{0}".format(MAP[parameter_value]))

                # Add command parameter
                elif not isinstance(parameter_value, bool):
                    if parameter_name in self.optional:
                        self.cmd.append("--{0}={1}".format(
                            cmd_parameter_name, parameter_value))
                    else:
                        self.cmd.append("-{0}".format(cmd_parameter_name))
                        self.cmd.append("{0}".format(parameter_value))

        # Add the sources
        for source in input_sources:
            self.cmd.append("{0}".format(source))
