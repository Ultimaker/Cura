import os.path
import json

from PyQt5.QtCore import QObject, QUrl, pyqtProperty, pyqtSignal, pyqtSlot
from PyQt5.QtQml import QQmlComponent, QQmlContext

from UM.Message import Message
from UM.Logger import Logger

from UM.Application import Application
from UM.Preferences import Preferences
from UM.Extension import Extension
from UM.PluginRegistry import PluginRegistry
from UM.OutputDevice.OutputDevicePlugin import OutputDevicePlugin

from . import OctoPrintOutputDevice
from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")


class OctoPrintExtension(QObject, Extension, OutputDevicePlugin):
    def __init__(self, parent = None):
        QObject.__init__(self, parent)
        Extension.__init__(self)
        OutputDevicePlugin.__init__(self)
        self.addMenuItem(catalog.i18n("OctoPrint Servers"), self.showSettingsDialog)
        self._dialogs = {}
        self._dialogView = None

        Preferences.getInstance().addPreference("octoprint/instances", json.dumps({}))
        self._instances = json.loads(Preferences.getInstance().getValue("octoprint/instances"))
        Logger.log("i", "self._instances %s", repr(self._instances))

    def start(self):
        manager = self.getOutputDeviceManager()
        Logger.log("i", "self._instances %s", repr(self._instances))
        for name, instance in self._instances.items():
            manager.addOutputDevice(OctoPrintOutputDevice.OctoPrintOutputDevice(name, instance["url"], instance["apikey"]))

    def stop(self):
        manager = self.getOutputDeviceManager()
        for name in self._instances.keys():
            manager.removeOutputDevice(name)

    def _createDialog(self, qml):
        path = QUrl.fromLocalFile(os.path.join(PluginRegistry.getInstance().getPluginPath("OctoPrintOutputDevice"), qml))
        self._component = QQmlComponent(Application.getInstance()._engine, path)
        self._context = QQmlContext(Application.getInstance()._engine.rootContext())
        self._context.setContextProperty("manager", self)
        dialog = self._component.create(self._context)
        if dialog is None:
            Logger.log("e", "QQmlComponent status %s", self._component.status())
            Logger.log("e", "QQmlComponent errorString %s", self._component.errorString())
            raise RuntimeError(self._component.errorString())
        return dialog

    def _showDialog(self, qml):
        if not qml in self._dialogs:
            self._dialogs[qml] = self._createDialog(qml)
        self._dialogs[qml].show()

    def showSettingsDialog(self):
        self._showDialog("OctoPrintPlugin.qml")

    serverListChanged = pyqtSignal()
    @pyqtProperty("QVariantList", notify = serverListChanged)
    def serverList(self):
        return list(self._instances.keys())

    @pyqtSlot(str, result = str)
    def instanceUrl(self, name):
        if name in self._instances.keys():
            return self._instances[name]["url"]
        return None

    @pyqtSlot(str, result = str)
    def instanceApiKey(self, name):
        if name in self._instances.keys():
            return self._instances[name]["apikey"]
        return None

    @pyqtSlot(str, str, str, str)
    def saveInstance(self, oldName, name, url, apiKey):
        manager = self.getOutputDeviceManager()
        if oldName and oldName != name:
            manager.removeOutputDevice(oldName)
            del self._instances[oldName]
        self._instances[name] = {
            "url": url,
            "apikey": apiKey
        }
        manager.addOutputDevice(OctoPrintOutputDevice.OctoPrintOutputDevice(name, url, apiKey))
        Preferences.getInstance().setValue("octoprint/instances", json.dumps(self._instances))
        self.serverListChanged.emit()

    @pyqtSlot(str)
    def removeInstance(self, name):
        self.getOutputDeviceManager().removeOutputDevice(name)
        del self._instances[name]
        Preferences.getInstance().setValue("octoprint/instances", json.dumps(self._instances))
        self.serverListChanged.emit()

    @pyqtSlot(str, str, result = bool)
    def validName(self, oldName, newName):
        # empty string isn't allowed
        if not newName:
            return False
        # if name hasn't changed, not a duplicate, just no rename
        if oldName == newName:
            return True

        # duplicates not allowed
        return (not newName in self._instances.keys())

