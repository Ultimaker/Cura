# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from . import UserAgreement

def getMetaData():
    return {}

def register(app):
    return {"extension": UserAgreement.UserAgreement(app)}
