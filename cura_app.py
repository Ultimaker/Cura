#!/usr/bin/env python3

# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

import sys

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
