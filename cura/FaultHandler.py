# Copyright (c) 2026 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

import faulthandler
import sys


def enableFaultHandler() -> None:
    # Windows can invoke the native exception handler without the GIL while
    # other Python threads are running. Dumping their changing frames can
    # itself crash Cura (see #21121). Keep faulting-thread diagnostics there.
    all_threads = sys.platform != "win32"
    if sys.stderr and not sys.stderr.closed:
        faulthandler.enable(file = sys.stderr, all_threads = all_threads)
    elif sys.stdout and not sys.stdout.closed:
        faulthandler.enable(file = sys.stdout, all_threads = all_threads)
