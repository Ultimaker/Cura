# Copyright (c) 2018 Ultimaker B.V.
# Toolbox is released under the terms of the LGPLv3 or higher.

from .src import Toolbox
from .src.SubscriptionChecker import SubscriptionChecker


def getMetaData():
    return {}


def register(app):
    return {
        "extension": Toolbox.Toolbox(app),
        "subscription_checker": SubscriptionChecker(app)
    }
