#!/usr/bin/env python3

# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

try:
    import cura.CuraApplication

    app = cura.CuraApplication.CuraApplication.getInstance()
    app.run()
except Exception as e:
    import cura.CrashHandler
    cura.CrashHandler.show()

