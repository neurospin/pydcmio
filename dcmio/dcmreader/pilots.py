#! /usr/bin/env python
##########################################################################
# CAPS - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
import datetime

# CAPS import
from caps.toy_datasets import get_sample_data

# Lib import
from dcmreader import get_sequence_name, get_all_sop_instance_uids

start_time = datetime.datetime.now()

localizer_dataset = get_sample_data("qt1")
#
print "Start Procedure", start_time
print "***************"
print ""
print "Extracting sequence name (first value returned only)..."
seqname = get_sequence_name(localizer_dataset.gre5dcm)
print "sequence name: {0}".format(seqname)
print ""
print ("Extracting Referenced SOP Instance UID (all values "
       "returned in a list)...")
uids = get_all_sop_instance_uids(localizer_dataset.gre20dcm)
print "Referenced SOP Instance UID: {0}".format(uids)
print ""

print "End of pilots"
print "Done in {0} seconds.".format(datetime.datetime.now() - start_time)
print "*************************"
