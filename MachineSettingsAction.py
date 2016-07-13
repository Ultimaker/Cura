from cura.MachineAction import MachineAction
import cura.Settings.CuraContainerRegistry

from UM.i18n import i18nCatalog
from UM.Settings.DefinitionContainer import DefinitionContainer
from UM.Application import Application

from PyQt5.QtCore import  pyqtSlot, QObject


catalog = i18nCatalog("cura")

class MachineSettingsAction(MachineAction, QObject):
    def __init__(self, parent = None):
        MachineAction.__init__(self, "MachineSettingsAction", catalog.i18nc("@action", "Machine Settings"))
        self._qml_url = "MachineSettingsAction.qml"

        cura.Settings.CuraContainerRegistry.getInstance().containerAdded.connect(self._onContainerAdded)

    def _execute(self):
        pass

    def _reset(self):
        pass

    def _onContainerAdded(self, container):
        # Add this action as a supported action to all machine definitions
        if isinstance(container, DefinitionContainer) and container.getMetaDataEntry("type") == "machine":
            Application.getInstance().getMachineActionManager().addSupportedAction(container.getId(), self.getKey())

    @pyqtSlot()
    def forceUpdate(self):
        # Force rebuilding the build volume by reloading the global container stack.
        # This is a bit of a hack, but it seems quick enough.
        Application.getInstance().globalContainerStackChanged.emit()