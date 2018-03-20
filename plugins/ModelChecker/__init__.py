# Copyright (c) 2017 Ultimaker B.V.
# This example is released under the terms of the AGPLv3 or higher.

from . import ModelChecker

from UM.i18n import i18nCatalog
i18n_catalog = i18nCatalog("uranium")


def getMetaData():
    return {
        "tool": {
            "name": i18n_catalog.i18nc("@label", "Model Checker"),
            "description": i18n_catalog.i18nc("@info:tooltip", "Checks models and print configuration for possible printing issues and give suggestions."),
            "icon": "model_checker.svg",
            "weight": 10
        }
    }

def register(app):
    return { "tool": ModelChecker.ModelChecker() }
