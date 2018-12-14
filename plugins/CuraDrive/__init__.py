# Copyright (c) 2017 Ultimaker B.V.
import os

is_testing = os.getenv('ENV_NAME', "development") == "testing"

# Only load the whole plugin when not running tests as __init__.py is automatically loaded by PyTest
if not is_testing:
    from .src.DrivePluginExtension import DrivePluginExtension

    def getMetaData():
        return {}

    def register(app):
        return {"extension": DrivePluginExtension(app)}
