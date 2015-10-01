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
    import os.path
    sys.stdout = open(os.path.expanduser("~/AppData/Local/cura/stdout.log"), "w")
    sys.stderr = open(os.path.expanduser("~/AppData/Local/cura/stderr.log"), "w")

app = cura.CuraApplication.CuraApplication.getInstance()
app.run()
