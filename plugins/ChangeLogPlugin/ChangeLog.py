# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from UM.i18n import i18nCatalog
from UM.Extension import Extension
from UM.Preferences import Preferences
from UM.Application import Application
from UM.PluginRegistry import PluginRegistry
from UM.Version import Version

from PyQt5.QtQuick import QQuickView
from PyQt5.QtQml import QQmlComponent, QQmlContext
from PyQt5.QtCore import QUrl, pyqtSlot, QObject

import os.path
import collections

catalog = i18nCatalog("cura")

class ChangeLog(Extension, QObject,):
    def __init__(self, parent = None):
        QObject.__init__(self, parent)
        Extension.__init__(self)
        self._changelog_window = None
        self._changelog_context = None
        version_string = Application.getInstance().getVersion()
        if version_string is not "master":
            self._version = Version(version_string)
        else:
            self._version = None
        self._change_logs = None
        Application.getInstance().engineCreatedSignal.connect(self._onEngineCreated)
        Preferences.getInstance().addPreference("general/latest_version_changelog_shown", "15.05.90") #First version of CURA with uranium
        self.addMenuItem(catalog.i18nc("@item:inmenu", "Show Changelog"), self.showChangelog)
        #self.showChangelog()

    def getChangeLogs(self):
        if not self._change_logs:
            self.loadChangeLogs()
        return self._change_logs

    @pyqtSlot(result = str)
    def getChangeLogString(self):
        logs = self.getChangeLogs()
        latest_version = Version(Preferences.getInstance().getValue("general/latest_version_changelog_shown")) #TODO: @UnusedVariable
        result = ""
        for version in logs:
            result += "<h1>" + str(version) + "</h1><br>"
            result += ""
            for change in logs[version]:
                result += "<b>" + str(change) + "</b><br>"
                for line in logs[version][change]:
                    result += str(line) + "<br>"
                result += "<br>"

        pass
        return result

    def loadChangeLogs(self):
        self._change_logs = collections.OrderedDict()
        with open(os.path.join(PluginRegistry.getInstance().getPluginPath("ChangeLogPlugin"), "ChangeLog.txt"), "r",-1, "utf-8") as f:
            open_version = None
            open_header = None
            for line in f:
                line = line.replace("\n","")
                if "[" in line and "]" in line:
                    line = line.replace("[","")
                    line = line.replace("]","")
                    open_version = Version(line)
                    self._change_logs[Version(line)] = collections.OrderedDict()
                elif line.startswith("*"):
                    open_header = line.replace("*","")
                    self._change_logs[open_version][open_header] = []
                else:
                    if line != "":
                        self._change_logs[open_version][open_header].append(line)

    def _onEngineCreated(self):
        if not self._version:
            return #We're on dev branch.
        #if self._version > Preferences.getInstance().getValue("general/latest_version_changelog_shown"):
            #self.showChangelog()

    def showChangelog(self):
        if not self._changelog_window:
            self.createChangelogWindow()
        self._changelog_window.show()
        Preferences.getInstance().setValue("general/latest_version_changelog_shown", Application.getInstance().getVersion())

    def hideChangelog(self):
        if self._changelog_window:
            self._changelog_window.hide()

    def createChangelogWindow(self):
        path = QUrl.fromLocalFile(os.path.join(PluginRegistry.getInstance().getPluginPath("ChangeLogPlugin"), "ChangeLog.qml"))
        component = QQmlComponent(Application.getInstance()._engine, path)
        self._changelog_context = QQmlContext(Application.getInstance()._engine.rootContext())
        self._changelog_context.setContextProperty("manager", self)
        self._changelog_window = component.create(self._changelog_context)
        #print(self._changelog_window)
