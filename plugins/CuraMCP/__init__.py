from . import CuraMCPPlugin


def getMetaData():
    return {}


def register(app):
    return {"extension": CuraMCPPlugin.CuraMCPPlugin()}
