// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

pragma Singleton

import QtQuick 2.2
import QtQuick.Controls 1.1
import UM 1.1 as UM
import Cura 1.0 as Cura

Item
{
    property alias newProject: newProjectAction;
    property alias open: openAction;
    property alias quit: quitAction;

    property alias undo: undoAction;
    property alias redo: redoAction;

    property alias view3DCamera: view3DCameraAction;
    property alias viewFrontCamera: viewFrontCameraAction;
    property alias viewTopCamera: viewTopCameraAction;
    property alias viewLeftSideCamera: viewLeftSideCameraAction;
    property alias viewRightSideCamera: viewRightSideCameraAction;

    property alias deleteSelection: deleteSelectionAction;
    property alias centerSelection: centerSelectionAction;
    property alias multiplySelection: multiplySelectionAction;

    property alias deleteObject: deleteObjectAction;
    property alias centerObject: centerObjectAction;
    property alias groupObjects: groupObjectsAction;
    property alias unGroupObjects:unGroupObjectsAction;
    property alias mergeObjects: mergeObjectsAction;
    //property alias unMergeObjects: unMergeObjectsAction;

    property alias multiplyObject: multiplyObjectAction;

    property alias selectAll: selectAllAction;
    property alias deleteAll: deleteAllAction;
    property alias reloadAll: reloadAllAction;
    property alias arrangeAllBuildPlates: arrangeAllBuildPlatesAction;
    property alias arrangeAll: arrangeAllAction;
    property alias arrangeSelection: arrangeSelectionAction;
    property alias resetAllTranslation: resetAllTranslationAction;
    property alias resetAll: resetAllAction;

    property alias addMachine: addMachineAction;
    property alias configureMachines: settingsAction;
    property alias addProfile: addProfileAction;
    property alias updateProfile: updateProfileAction;
    property alias resetProfile: resetProfileAction;
    property alias manageProfiles: manageProfilesAction;

    property alias manageMaterials: manageMaterialsAction;

    property alias preferences: preferencesAction;

    property alias showProfileFolder: showProfileFolderAction;
    property alias documentation: documentationAction;
    property alias showTroubleshooting: showTroubleShootingAction
    property alias reportBug: reportBugAction;
    property alias about: aboutAction;

    property alias toggleFullScreen: toggleFullScreenAction;

    property alias configureSettingVisibility: configureSettingVisibilityAction

    property alias browsePackages: browsePackagesAction

    UM.I18nCatalog{id: catalog; name: "cura"}


    Action
    {
        id: showTroubleShootingAction
        onTriggered: Qt.openUrlExternally("https://ultimaker.com/en/troubleshooting")
        text: catalog.i18nc("@action:inmenu", "Show Online Troubleshooting Guide");
    }

    Action
    {
        id:toggleFullScreenAction
        shortcut: StandardKey.FullScreen;
        text: catalog.i18nc("@action:inmenu", "Toggle Full Screen");
        iconName: "view-fullscreen";
    }

    Action
    {
        id: undoAction;
        text: catalog.i18nc("@action:inmenu menubar:edit", "&Undo");
        iconName: "edit-undo";
        shortcut: StandardKey.Undo;
        onTriggered: UM.OperationStack.undo();
        enabled: UM.OperationStack.canUndo;
    }

    Action
    {
        id: redoAction;
        text: catalog.i18nc("@action:inmenu menubar:edit","&Redo");
        iconName: "edit-redo";
        shortcut: StandardKey.Redo;
        onTriggered: UM.OperationStack.redo();
        enabled: UM.OperationStack.canRedo;
    }

    Action
    {
        id: quitAction;
        text: catalog.i18nc("@action:inmenu menubar:file","&Quit");
        iconName: "application-exit";
        shortcut: StandardKey.Quit;
    }

    Action
    {
        id: view3DCameraAction;
        text: catalog.i18nc("@action:inmenu menubar:view","3D View");
        onTriggered: UM.Controller.rotateView("3d", 0);
    }

    Action
    {
        id: viewFrontCameraAction;
        text: catalog.i18nc("@action:inmenu menubar:view","Front View");
        onTriggered: UM.Controller.rotateView("home", 0);
    }

    Action
    {
        id: viewTopCameraAction;
        text: catalog.i18nc("@action:inmenu menubar:view","Top View");
        onTriggered: UM.Controller.rotateView("y", 90);
    }

    Action
    {
        id: viewLeftSideCameraAction;
        text: catalog.i18nc("@action:inmenu menubar:view","Left Side View");
        onTriggered: UM.Controller.rotateView("x", 90);
    }

    Action
    {
        id: viewRightSideCameraAction;
        text: catalog.i18nc("@action:inmenu menubar:view","Right Side View");
        onTriggered: UM.Controller.rotateView("x", -90);
    }

    Action
    {
        id: preferencesAction;
        text: catalog.i18nc("@action:inmenu","Configure Cura...");
        iconName: "configure";
    }

    Action
    {
        id: addMachineAction;
        text: catalog.i18nc("@action:inmenu menubar:printer","&Add Printer...");
    }

    Action
    {
        id: settingsAction;
        text: catalog.i18nc("@action:inmenu menubar:printer","Manage Pr&inters...");
        iconName: "configure";
    }

    Action
    {
        id: manageMaterialsAction
        text: catalog.i18nc("@action:inmenu", "Manage Materials...")
        iconName: "configure"
        shortcut: "Ctrl+K"
    }

    Action
    {
        id: updateProfileAction;
        enabled: !Cura.MachineManager.stacksHaveErrors && Cura.MachineManager.hasUserSettings && Cura.MachineManager.activeQualityChangesGroup != null
        text: catalog.i18nc("@action:inmenu menubar:profile","&Update profile with current settings/overrides");
        onTriggered: Cura.ContainerManager.updateQualityChanges();
    }

    Action
    {
        id: resetProfileAction;
        enabled: Cura.MachineManager.hasUserSettings
        text: catalog.i18nc("@action:inmenu menubar:profile", "&Discard current changes");
        onTriggered:
        {
            forceActiveFocus();
            Cura.ContainerManager.clearUserContainers();
        }
    }

    Action
    {
        id: addProfileAction;
        enabled: !Cura.MachineManager.stacksHaveErrors && Cura.MachineManager.hasUserSettings
        text: catalog.i18nc("@action:inmenu menubar:profile", "&Create profile from current settings/overrides...");
    }

    Action
    {
        id: manageProfilesAction
        text: catalog.i18nc("@action:inmenu menubar:profile", "Manage Profiles...")
        iconName: "configure"
        shortcut: "Ctrl+J"
    }

    Action
    {
        id: documentationAction;
        text: catalog.i18nc("@action:inmenu menubar:help", "Show Online &Documentation");
        iconName: "help-contents";
        shortcut: StandardKey.Help;
        onTriggered: CuraActions.openDocumentation();
    }

    Action {
        id: reportBugAction;
        text: catalog.i18nc("@action:inmenu menubar:help", "Report a &Bug");
        iconName: "tools-report-bug";
        onTriggered: CuraActions.openBugReportPage();
    }

    Action
    {
        id: aboutAction;
        text: catalog.i18nc("@action:inmenu menubar:help", "About...");
        iconName: "help-about";
    }

    Action
    {
        id: deleteSelectionAction;
        text: catalog.i18ncp("@action:inmenu menubar:edit", "Delete Selected Model", "Delete Selected Models", UM.Selection.selectionCount);
        enabled: UM.Controller.toolsEnabled && UM.Selection.hasSelection;
        iconName: "edit-delete";
        shortcut: StandardKey.Delete;
        onTriggered: CuraActions.deleteSelection();
    }

    Action
    {
        id: centerSelectionAction;
        text: catalog.i18ncp("@action:inmenu menubar:edit", "Center Selected Model", "Center Selected Models", UM.Selection.selectionCount);
        enabled: UM.Controller.toolsEnabled && UM.Selection.hasSelection;
        iconName: "align-vertical-center";
        onTriggered: CuraActions.centerSelection();
    }

    Action
    {
        id: multiplySelectionAction;
        text: catalog.i18ncp("@action:inmenu menubar:edit", "Multiply Selected Model", "Multiply Selected Models", UM.Selection.selectionCount);
        enabled: UM.Controller.toolsEnabled && UM.Selection.hasSelection;
        iconName: "edit-duplicate";
        shortcut: "Ctrl+M"
    }

    Action
    {
        id: deleteObjectAction;
        text: catalog.i18nc("@action:inmenu","Delete Model");
        enabled: UM.Controller.toolsEnabled;
        iconName: "edit-delete";
    }

    Action
    {
        id: centerObjectAction;
        text: catalog.i18nc("@action:inmenu","Ce&nter Model on Platform");
    }

    Action
    {
        id: groupObjectsAction
        text: catalog.i18nc("@action:inmenu menubar:edit","&Group Models");
        enabled: UM.Scene.numObjectsSelected > 1 ? true: false
        iconName: "object-group"
        shortcut: "Ctrl+G";
        onTriggered: CuraApplication.groupSelected();
    }

    Action
    {
        id: reloadQmlAction
        onTriggered:
        {
            CuraApplication.reloadQML()
        }
        shortcut: "Shift+F5"
    }

    Action
    {
        id: unGroupObjectsAction
        text: catalog.i18nc("@action:inmenu menubar:edit","Ungroup Models");
        enabled: UM.Scene.isGroupSelected
        iconName: "object-ungroup"
        shortcut: "Ctrl+Shift+G";
        onTriggered: CuraApplication.ungroupSelected();
    }

    Action
    {
        id: mergeObjectsAction
        text: catalog.i18nc("@action:inmenu menubar:edit","&Merge Models");
        enabled: UM.Scene.numObjectsSelected > 1 ? true: false
        iconName: "merge";
        shortcut: "Ctrl+Alt+G";
        onTriggered: CuraApplication.mergeSelected();
    }

    Action
    {
        id: multiplyObjectAction;
        text: catalog.i18nc("@action:inmenu","&Multiply Model...");
        iconName: "edit-duplicate"
    }

    Action
    {
        id: selectAllAction;
        text: catalog.i18nc("@action:inmenu menubar:edit","Select All Models");
        enabled: UM.Controller.toolsEnabled;
        iconName: "edit-select-all";
        shortcut: "Ctrl+A";
        onTriggered: CuraApplication.selectAll();
    }

    Action
    {
        id: deleteAllAction;
        text: catalog.i18nc("@action:inmenu menubar:edit","Clear Build Plate");
        enabled: UM.Controller.toolsEnabled;
        iconName: "edit-delete";
        shortcut: "Ctrl+D";
        onTriggered: CuraApplication.deleteAll();
    }

    Action
    {
        id: reloadAllAction;
        text: catalog.i18nc("@action:inmenu menubar:file","Reload All Models");
        iconName: "document-revert";
        shortcut: "F5"
        onTriggered: CuraApplication.reloadAll();
    }

    Action
    {
        id: arrangeAllBuildPlatesAction;
        text: catalog.i18nc("@action:inmenu menubar:edit","Arrange All Models To All Build Plates");
        onTriggered: Printer.arrangeObjectsToAllBuildPlates();
    }

    Action
    {
        id: arrangeAllAction;
        text: catalog.i18nc("@action:inmenu menubar:edit","Arrange All Models");
        onTriggered: Printer.arrangeAll();
        shortcut: "Ctrl+R";
    }

    Action
    {
        id: arrangeSelectionAction;
        text: catalog.i18nc("@action:inmenu menubar:edit","Arrange Selection");
        onTriggered: Printer.arrangeSelection();
    }

    Action
    {
        id: resetAllTranslationAction;
        text: catalog.i18nc("@action:inmenu menubar:edit","Reset All Model Positions");
        onTriggered: CuraApplication.resetAllTranslation();
    }

    Action
    {
        id: resetAllAction;
        text: catalog.i18nc("@action:inmenu menubar:edit","Reset All Model Transformations");
        onTriggered: CuraApplication.resetAll();
    }

    Action
    {
        id: openAction;
        text: catalog.i18nc("@action:inmenu menubar:file","&Open File(s)...");
        iconName: "document-open";
        shortcut: StandardKey.Open;
    }

    Action
    {
        id: newProjectAction
        text: catalog.i18nc("@action:inmenu menubar:file","&New Project...");
        shortcut: StandardKey.New
    }

    Action
    {
        id: showProfileFolderAction;
        text: catalog.i18nc("@action:inmenu menubar:help","Show Configuration Folder");
    }


    Action
    {
        id: configureSettingVisibilityAction
        text: catalog.i18nc("@action:menu", "Configure setting visibility...");
        iconName: "configure"
    }

    Action
    {
        id: browsePackagesAction
        text: catalog.i18nc("@action:menu", "&Marketplace")
        iconName: "plugins_browse"
    }
}
