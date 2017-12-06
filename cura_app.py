#!/usr/bin/env python3

# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
import os
import sys
import platform
import faulthandler

from UM.Platform import Platform

#WORKAROUND: GITHUB-88 GITHUB-385 GITHUB-612
if Platform.isLinux(): # Needed for platform.linux_distribution, which is not available on Windows and OSX
    # For Ubuntu: https://bugs.launchpad.net/ubuntu/+source/python-qt4/+bug/941826
    if platform.linux_distribution()[0] in ("debian", "Ubuntu", "LinuxMint"): # TODO: Needs a "if X11_GFX == 'nvidia'" here. The workaround is only needed on Ubuntu+NVidia drivers. Other drivers are not affected, but fine with this fix.
        import ctypes
        from ctypes.util import find_library
        libGL = find_library("GL")
        ctypes.CDLL(libGL, ctypes.RTLD_GLOBAL)

# When frozen, i.e. installer version, don't let PYTHONPATH mess up the search path for DLLs.
if Platform.isWindows() and hasattr(sys, "frozen"):
    try:
        del os.environ["PYTHONPATH"]
    except KeyError: pass

#WORKAROUND: GITHUB-704 GITHUB-708
# It looks like setuptools creates a .pth file in
# the default /usr/lib which causes the default site-packages
# to be inserted into sys.path before PYTHONPATH.
# This can cause issues such as having libsip loaded from
# the system instead of the one provided with Cura, which causes
# incompatibility issues with libArcus
if "PYTHONPATH" in os.environ.keys():                       # If PYTHONPATH is used
    PYTHONPATH = os.environ["PYTHONPATH"].split(os.pathsep) # Get the value, split it..
    PYTHONPATH.reverse()                                    # and reverse it, because we always insert at 1
    for PATH in PYTHONPATH:                                 # Now beginning with the last PATH
        PATH_real = os.path.realpath(PATH)                  # Making the the path "real"
        if PATH_real in sys.path:                           # This should always work, but keep it to be sure..
            sys.path.remove(PATH_real)
        sys.path.insert(1, PATH_real)                       # Insert it at 1 after os.curdir, which is 0.

def exceptHook(hook_type, value, traceback):
    from cura.CrashHandler import CrashHandler
    _crash_handler = CrashHandler(hook_type, value, traceback)
    _crash_handler.show()

sys.excepthook = exceptHook

# Workaround for a race condition on certain systems where there
# is a race condition between Arcus and PyQt. Importing Arcus
# first seems to prevent Sip from going into a state where it
# tries to create PyQt objects on a non-main thread.
import Arcus #@UnusedImport
import cura.CuraApplication
import cura.Settings.CuraContainerRegistry

def get_cura_dir_path():
    if Platform.isWindows():
        return os.path.expanduser("~/AppData/Local/cura/")
    elif Platform.isLinux():
        return os.path.expanduser("~/.local/share/cura")
    elif Platform.isOSX():
        return os.path.expanduser("~/Library/Logs/cura")


if hasattr(sys, "frozen"):
    dirpath = get_cura_dir_path()
    os.makedirs(dirpath, exist_ok = True)
    sys.stdout = open(os.path.join(dirpath, "stdout.log"), "w")
    sys.stderr = open(os.path.join(dirpath, "stderr.log"), "w")

faulthandler.enable()

# Force an instance of CuraContainerRegistry to be created and reused later.
cura.Settings.CuraContainerRegistry.CuraContainerRegistry.getInstance()

# This prestart up check is needed to determine if we should start the application at all.
if not cura.CuraApplication.CuraApplication.preStartUp():
    sys.exit(0)

app = cura.CuraApplication.CuraApplication.getInstance()
app.run()
