# Copyright (c) 2024 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import TYPE_CHECKING, Optional

from UM.Backend.Backend import BackendState
from UM.Logger import Logger

if TYPE_CHECKING:
    from cura.CuraApplication import CuraApplication
    from UM.Settings.ContainerStack import ContainerStack


class SafeWorkspaceChecker:
    """Manages the 'safe workspace' feature.

    When enabled via the ``cura/safe_workspace_enabled`` preference this class
    registers itself as an on-exit callback and shows a dialog before the
    application closes whenever:

    * There are models on the build plate and the workspace has been modified
      since the last successful save, OR
    * The backend has produced a slice result that has not yet been exported, OR
    * The backend is currently slicing (closing would abort the in-progress slice).
    """

    def __init__(self, application: "CuraApplication") -> None:
        self._application = application

        self._workspace_needs_saving: bool = False
        self._slice_exported: bool = True
        self._is_slicing: bool = False
        self._pending_workspace_save: bool = False

        application.getOnExitCallbackManager().addCallback(self._checkSafeWorkspaceOnExit)
        application.getOperationStack().changed.connect(self._onOperationStackChanged)
        application.globalContainerStackChanged.connect(self._onGlobalStackChanged)
        application.workspaceLoaded.connect(self._onWorkspaceLoaded)

        self._global_stack: Optional["ContainerStack"] = None
        self._onGlobalStackChanged()

        application.engineCreatedSignal.connect(self._onEngineCreated)

    def _onEngineCreated(self) -> None:
        backend = self._application.getBackend()
        if backend is not None:
            backend.backendStateChange.connect(self._onBackendStateChanged)

        self._application.getOutputDeviceManager().writeSuccess.connect(self._onWriteSuccess)

        self._onGlobalStackChanged()

    def _onOperationStackChanged(self) -> None:
        """Mark workspace dirty whenever the operation stack changes."""
        if self._application.getloadingWorkspace():
            return
        if self._application.getOperationStack().canUndo():
            self._workspace_needs_saving = True

    def _onGlobalStackChanged(self) -> None:
        """Reconnect to the active global container stack's change signals."""
        if self._global_stack is not None:
            self._global_stack.propertyChanged.disconnect(self._onSettingsChanged)
            self._global_stack.containersChanged.disconnect(self._onSettingsChanged)

        self._global_stack = self._application.getGlobalContainerStack()

        if self._global_stack is not None:
            self._global_stack.propertyChanged.connect(self._onSettingsChanged)
            self._global_stack.containersChanged.connect(self._onSettingsChanged)

    def _onSettingsChanged(self, *args) -> None:
        """Mark workspace dirty when any printer setting or container changes."""
        if self._application.getloadingWorkspace():
            return
        self._workspace_needs_saving = True

    def _onWorkspaceLoaded(self, path: str = "") -> None:
        """A workspace was just loaded — it starts clean (no unsaved changes)."""
        self._workspace_needs_saving = False

    def _onBackendStateChanged(self, state: int) -> None:
        """Track when a fresh slice result appears or disappears."""
        self._is_slicing = (state == BackendState.Processing)
        if state == BackendState.Done:
            self._slice_exported = False
        elif state in (BackendState.NotStarted, BackendState.Processing, BackendState.Error):
            self._slice_exported = True

    def _onWriteSuccess(self, device) -> None:
        """Called when any output device finishes a successful write."""
        if self._pending_workspace_save:
            self._pending_workspace_save = False
            if self._close_after_save:
                self._application.callLater(self._finishSaveAndClose)
            else:
                self._workspace_needs_saving = False
        else:
            self._slice_exported = True
            if self._close_after_export:
                self._application.callLater(self._application.checkAndExitApplication)

    def _finishSaveAndClose(self) -> None:
        """Deferred: clear the dirty flag then restart the exit check."""
        self._workspace_needs_saving = False
        self._application.checkAndExitApplication()


    def markPendingWorkspaceSave(self) -> None:
        """Call this just before triggering a workspace write operation."""
        self._pending_workspace_save = True

    def markPendingWorkspaceSaveAndClose(self) -> None:
        """Like markPendingWorkspaceSave, but also re-triggers the exit flow on success."""
        self._pending_workspace_save = True
        self._close_after_save = True

    def markSliceExportAndClose(self) -> None:
        """Call before triggering a slice export from the safe workspace dialog."""
        self._close_after_export = True

    def clearPendingWorkspaceSave(self) -> None:
        """Call this if a workspace write was cancelled or failed."""
        self._pending_workspace_save = False
        self._close_after_save = False
        self._close_after_export = False

    def _checkSafeWorkspaceOnExit(self) -> None:
        """On-exit callback: show the safe-workspace dialog when needed."""
        application = self._application

        if not application.getPreferences().getValue("cura/safe_workspace_enabled"):
            application.triggerNextExitCheck()
            return

        has_models: bool = len(application.getObjectsModel().getNodes()) > 0
        workspace_not_saved: bool = has_models and self._workspace_needs_saving

        slice_not_exported: bool = not self._slice_exported
        is_slicing: bool = self._is_slicing

        if not workspace_not_saved and not slice_not_exported and not is_slicing:
            application.triggerNextExitCheck()
            return

        Logger.info("SafeWorkspaceChecker: intercepting close. workspace_not_saved=%s slice_not_exported=%s is_slicing=%s",
                    workspace_not_saved, slice_not_exported, is_slicing)
        application.showSafeWorkspaceDialog.emit(workspace_not_saved, slice_not_exported, is_slicing)
