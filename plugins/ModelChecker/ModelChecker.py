# Copyright (c) 2026 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.
from ModelChecker.ModelCheckerJob import ModelCheckerJob
from cura.Settings.GlobalStack import GlobalStack

import os

from PyQt6.QtCore import QObject, pyqtSlot, pyqtSignal, pyqtProperty, QTimer

from UM.Application import Application
from UM.Backend.Backend import BackendState
from UM.Extension import Extension
from UM.Logger import Logger
from UM.Message import Message
from UM.Scene.Camera import Camera
from UM.i18n import i18nCatalog
from UM.PluginRegistry import PluginRegistry

catalog = i18nCatalog("cura")


class ModelChecker(QObject, Extension):
    onChanged = pyqtSignal()
    """Signal that gets emitted when anything changed that we need to check."""

    onUpdated = pyqtSignal()
    """Signal that gets emitted when a warning is computed."""

    def __init__(self) -> None:
        super().__init__()

        self._button_view = None

        self._caution_message = Message("", #Message text gets set when the message gets shown, to display the models in question.
            lifetime = 0,
            title = catalog.i18nc("@info:title", "3D Model Assistant"),
            message_type = Message.MessageType.WARNING)
        self._caution_message.actionTriggered.connect(self._onMessageActionTriggered)

        self._change_timer = QTimer()
        self._change_timer.setInterval(200)
        self._change_timer.setSingleShot(True)
        self._change_timer.timeout.connect(self._startJob)

        Application.getInstance().initializationFinished.connect(self._pluginsInitialized)
        Application.getInstance().getController().getScene().sceneChanged.connect(self._onChanged)
        Application.getInstance().globalContainerStackChanged.connect(self._onChanged)

        self._unhandled_slice = False
        Application.getInstance().getBackend().backendStateChange.connect(self._onSliceState)

        self._last_checker_job = None
        self._current_warnings = {}

    def _onSliceState(self, state: BackendState) -> None:
        self._unhandled_slice |= (state == BackendState.Processing)
        self._onChanged()

    def _onChanged(self, *args, **kwargs) -> None:
        if len(args) != 0 and isinstance(args[0], Camera):  # Ignore camera updates.
            return
        self._change_timer.start()

    def _pluginsInitialized(self) -> None:
        """Called when plug-ins are initialized.

        This makes sure that we listen to changes of the material and that the
        button is created that indicates warnings with the current set-up.
        """

        Application.getInstance().getMachineManager().rootMaterialChanged.connect(self.onChanged)
        self._createView()

    def _onMessageActionTriggered(self, message: Message, message_action: str) -> None:
        if message_action == "enable_support":
            message.hide()
            global_container_stack: GlobalStack = Application.getInstance().getGlobalContainerStack()
            if not global_container_stack:
                return
            global_container_stack.setProperty("support_enable", "value", True)

    def _createView(self) -> None:
        """Creates the view used by show popup.

        The view is saved because of the fairly aggressive garbage collection.
        """

        Logger.log("d", "Creating model checker view.")

        # Create the plugin dialog component
        path = os.path.join(PluginRegistry.getInstance().getPluginPath("ModelChecker"), "ModelChecker.qml")
        self._button_view = Application.getInstance().createQmlComponent(path, {"manager": self})

        # The qml is only the button
        Application.getInstance().addAdditionalComponent("jobSpecsButton", self._button_view)

        Logger.log("d", "Model checker view created.")

    @pyqtProperty(bool, notify = onUpdated)
    def hasWarnings(self) -> bool:
        return any(self._current_warnings.values())

    def _onCheckerJobFinished(self, *args):
        if not self._last_checker_job:
            return
        self._current_warnings.update(self._last_checker_job.getWarnings())
        self._last_checker_job = None
        self.onUpdated.emit()

    def _startJob(self) -> None:
        self._caution_message.getActions().clear()

        self._last_checker_job = ModelCheckerJob(self._caution_message, self._unhandled_slice)
        self._last_checker_job.needsRetry.connect(lambda: self.onChanged.emit())
        self._last_checker_job.finished.connect(self._onCheckerJobFinished)
        self._last_checker_job.start()

        self._unhandled_slice = False

    @pyqtSlot()
    def showWarnings(self) -> None:
        self._caution_message.show()
