#!/usr/bin/env python3

# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

import traceback

try:
    import cura.CuraApplication

    app = cura.CuraApplication.CuraApplication.getInstance()
    app.run()
except Exception as e:
    traceback.print_exc()
    import cura.CrashHandler
    cura.CrashHandler.show()

