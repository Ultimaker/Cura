# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import os.path

from PyQt5.QtCore import QObject

from UM.i18n import i18nCatalog
from UM.Extension import Extension
from UM.Application import Application
from UM.PluginRegistry import PluginRegistry
from UM.Version import Version

catalog = i18nCatalog("cura")


class ChangeLog(Extension, QObject):
    def __init__(self, parent = None):
        QObject.__init__(self, parent)
        Extension.__init__(self)
        self._changelog_window = None
        self._changelog_context = None
        version_string = Application.getInstance().getVersion()
        if version_string is not "master":
            self._current_app_version = Version(version_string)
        else:
            self._current_app_version = None

        Application.getInstance().engineCreatedSignal.connect(self._onEngineCreated)
        Application.getInstance().getPreferences().addPreference("general/latest_version_changelog_shown", "2.0.0") #First version of CURA with uranium
        self.setMenuName(catalog.i18nc("@item:inmenu", "Changelog"))
        self.addMenuItem(catalog.i18nc("@item:inmenu", "Show Changelog"), self.showChangelog)

    def _onEngineCreated(self):
        if not self._current_app_version:
            return #We're on dev branch.

        if Application.getInstance().getPreferences().getValue("general/latest_version_changelog_shown") == "master":
            latest_version_shown = Version("0.0.0")
        else:
            latest_version_shown = Version(Application.getInstance().getPreferences().getValue("general/latest_version_changelog_shown"))

        Application.getInstance().getPreferences().setValue("general/latest_version_changelog_shown", Application.getInstance().getVersion())

        # Do not show the changelog when there is no global container stack
        # This implies we are running Cura for the first time.
        if not Application.getInstance().getGlobalContainerStack():
            return

        if self._current_app_version > latest_version_shown:
            self.showChangelog()

    def showChangelog(self):
        if not self._changelog_window:
            self.createChangelogWindow()

        self._changelog_window.show()

    def hideChangelog(self):
        if self._changelog_window:
            self._changelog_window.hide()

    def createChangelogWindow(self):
        path = os.path.join(PluginRegistry.getInstance().getPluginPath(self.getPluginId()), "ChangeLog.qml")
        self._changelog_window = Application.getInstance().createQmlComponent(path, {"manager": self})
