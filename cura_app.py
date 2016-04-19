#!/usr/bin/env python3

# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

import os
import sys

# WORKAROUND: GITHUB-704 GITHUB-708
# It looks like setuptools creates a .pth file in
# the default /usr/lib which causes the default site-packages
# to be inserted into sys.path before PYTHONPATH.
# This can cause issues such as having libsip loaded from
# the system instead of the one provided with Cura, which causes
# incompatibility issues with libArcus
if "PYTHONPATH" in os.environ.keys():                # If PYTHONPATH is used
    if sys.path[-1] == os.environ["PYTHONPATH"]:     # .. check whether PYTHONPATH is placed incorrectly at the end of sys.path.
        sys.path.pop(-1)                             # If so remove that element..
        sys.path.insert(1, os.environ['PYTHONPATH']) # and add it at the correct place again.


def exceptHook(hook_type, value, traceback):
    import cura.CrashHandler
    cura.CrashHandler.show(hook_type, value, traceback)

sys.excepthook = exceptHook

# Workaround for a race condition on certain systems where there
# is a race condition between Arcus and PyQt. Importing Arcus
# first seems to prevent Sip from going into a state where it
# tries to create PyQt objects on a non-main thread.
import Arcus #@UnusedImport
import cura.CuraApplication

if sys.platform == "win32" and hasattr(sys, "frozen"):
    import os
    dirpath = os.path.expanduser("~/AppData/Local/cura/")
    os.makedirs(dirpath, exist_ok = True)
    sys.stdout = open(os.path.join(dirpath, "stdout.log"), "w")
    sys.stderr = open(os.path.join(dirpath, "stderr.log"), "w")

app = cura.CuraApplication.CuraApplication.getInstance()
app.run()
