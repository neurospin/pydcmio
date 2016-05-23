##########################################################################
# NSAp - Copyright (C) CEA, 2013 - 2016
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
import os
import json
import random


def transcode_sids(sids, transcoding_table):
    """ Transcode the subject identifiers.

    The transcoded subject identifier is generated randomly (12 digits random
    number between 100000000000 and 999999999999). The procedure checks
    if the subject identifier has already been transcoded.

    Parameters
    ----------
    sids: list of str (mandatory)
        the list of subject identifiers to be transcoded.
    transcoding_table: str (mandatory)
        the transcoding table in JSON format that will be updated if necessary.
    """
    # Load the transcoding table
    if not os.path.isfile(transcoding_table):
        raise ValueError("'{0}' is not a valid transcoding file.".format(
            transcoding_table))
    with open(transcoding_table, "rt") as open_file:
        transcoding = json.load(open_file)

    # Go through each subject id
    for sid in sids:

        # If the original ID is already in the transcoding table, use existing
        # transcodage
        if sid in transcoding:
            continue

        # Otherwise generates a new transcodage randomly
        else:
            transcoded_sid = str(random.randint(100000000000, 999999999999))
            while transcoded_sid in transcoding:
                transcoded_sid = str(
                    random.randint(100000000000, 999999999999))
            transcoding[sid] = transcoded_sid

    # Write the output transcoding table
    with open(transcoding_table, "wt") as open_file:
        json.dump(transcoding, open_file, indent=4)
