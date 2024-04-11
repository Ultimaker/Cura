# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from .src import DigitalFactoryFileProvider, DigitalFactoryOutputDevicePlugin, DigitalFactoryController


def getMetaData():
    return {}


def register(app):
    df_controller = DigitalFactoryController.DigitalFactoryController(app)
    return {
        "file_provider": DigitalFactoryFileProvider.DigitalFactoryFileProvider(df_controller),
        "output_device": DigitalFactoryOutputDevicePlugin.DigitalFactoryOutputDevicePlugin(df_controller)
    }
