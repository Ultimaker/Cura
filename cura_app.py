#!/usr/bin/env python3

# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

import sys

def exceptHook(type, value, traceback):
    import cura.CrashHandler
    cura.CrashHandler.show(type, value, traceback)

sys.excepthook = exceptHook

import cura.CuraApplication

if sys.platform == "win32" and hasattr(sys, "frozen"):
    from UM.Resources import Resources
    sys.stdout = open(Resources.getStoragePath(Resources.Resources, "stdout.log"), "w")
    sys.stderr = open(Resources.getStoragePath(Resources.Resources, "stderr.log"), "w")

app = cura.CuraApplication.CuraApplication.getInstance()
app.run()
