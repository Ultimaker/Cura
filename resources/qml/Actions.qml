// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

pragma Singleton

import QtQuick 2.2
import QtQuick.Controls 1.1
import UM 1.1 as UM
import Cura 1.0 as Cura

Item
{
    property alias open: openAction;
    property alias quit: quitAction;

    property alias undo: undoAction;
    property alias redo: redoAction;

    property alias deleteSelection: deleteSelectionAction;

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

    property alias showEngineLog: showEngineLogAction;
    property alias documentation: documentationAction;
    property alias reportBug: reportBugAction;
    property alias about: aboutAction;

    property alias toggleFullScreen: toggleFullScreenAction;

    property alias configureSettingVisibility: configureSettingVisibilityAction

    UM.I18nCatalog{id: catalog; name:"cura"}

    Action
    {
        id:toggleFullScreenAction
        text: catalog.i18nc("@action:inmenu","Toggle Fu&ll Screen");
        iconName: "view-fullscreen";
    }

    Action
    {
        id: undoAction;
        text: catalog.i18nc("@action:inmenu menubar:edit","&Undo");
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
    }

    Action
    {
        id: updateProfileAction;
        enabled: Cura.MachineManager.isActiveStackValid && Cura.MachineManager.hasUserSettings && !Cura.MachineManager.isReadOnly(Cura.MachineManager.activeQualityId)
        text: catalog.i18nc("@action:inmenu menubar:profile","&Update profile with current settings");
        onTriggered: Cura.MachineManager.updateQualityContainerFromUserContainer()
    }

    Action
    {
        id: resetProfileAction;
        enabled: Cura.MachineManager.hasUserSettings
        text: catalog.i18nc("@action:inmenu menubar:profile","&Discard current settings");
        onTriggered: Cura.MachineManager.clearUserSettings();
    }

    Action
    {
        id: addProfileAction;
        enabled: Cura.MachineManager.isActiveStackValid && Cura.MachineManager.hasUserSettings
        text: catalog.i18nc("@action:inmenu menubar:profile","&Create profile from current settings...");
    }

    Action
    {
        id: manageProfilesAction;
        text: catalog.i18nc("@action:inmenu menubar:profile","Manage Profiles...");
        iconName: "configure";
    }

    Action
    {
        id: documentationAction;
        text: catalog.i18nc("@action:inmenu menubar:help","Show Online &Documentation");
        iconName: "help-contents";
        shortcut: StandardKey.Help;
        onTriggered: CuraActions.openDocumentation();
    }

    Action {
        id: reportBugAction;
        text: catalog.i18nc("@action:inmenu menubar:help","Report a &Bug");
        iconName: "tools-report-bug";
        onTriggered: CuraActions.openBugReportPage();
    }

    Action
    {
        id: aboutAction;
        text: catalog.i18nc("@action:inmenu menubar:help","&About...");
        iconName: "help-about";
    }

    Action
    {
        id: deleteSelectionAction;
        text: catalog.i18nc("@action:inmenu menubar:edit","Delete &Selection");
        enabled: UM.Controller.toolsEnabled;
        iconName: "edit-delete";
        shortcut: StandardKey.Delete;
        onTriggered: Printer.deleteSelection();
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
        onTriggered: Printer.groupSelected();
    }

    Action
    {
        id: unGroupObjectsAction
        text: catalog.i18nc("@action:inmenu menubar:edit","Ungroup Models");
        enabled: UM.Scene.isGroupSelected
        iconName: "object-ungroup"
        shortcut: "Ctrl+Shift+G";
        onTriggered: Printer.ungroupSelected();
    }

    Action
    {
        id: mergeObjectsAction
        text: catalog.i18nc("@action:inmenu menubar:edit","&Merge Models");
        enabled: UM.Scene.numObjectsSelected > 1 ? true: false
        iconName: "merge";
        shortcut: "Ctrl+Alt+G";
        onTriggered: Printer.mergeSelected();
    }

    Action
    {
        id: multiplyObjectAction;
        text: catalog.i18nc("@action:inmenu","&Duplicate Model");
        iconName: "edit-duplicate"
    }

    Action
    {
        id: selectAllAction;
        text: catalog.i18nc("@action:inmenu menubar:edit","&Select All Models");
        enabled: UM.Controller.toolsEnabled;
        iconName: "edit-select-all";
        shortcut: "Ctrl+A";
        onTriggered: Printer.selectAll();
    }

    Action
    {
        id: deleteAllAction;
        text: catalog.i18nc("@action:inmenu menubar:edit","&Clear Build Plate");
        enabled: UM.Controller.toolsEnabled;
        iconName: "edit-delete";
        shortcut: "Ctrl+D";
        onTriggered: Printer.deleteAll();
    }

    Action
    {
        id: reloadAllAction;
        text: catalog.i18nc("@action:inmenu menubar:file","Re&load All Models");
        iconName: "document-revert";
        onTriggered: Printer.reloadAll();
    }

    Action
    {
        id: resetAllTranslationAction;
        text: catalog.i18nc("@action:inmenu menubar:edit","Reset All Model Positions");
        onTriggered: Printer.resetAllTranslation();
    }

    Action
    {
        id: resetAllAction;
        text: catalog.i18nc("@action:inmenu menubar:edit","Reset All Model &Transformations");
        onTriggered: Printer.resetAll();
    }

    Action
    {
        id: openAction;
        text: catalog.i18nc("@action:inmenu menubar:file","&Open File...");
        iconName: "document-open";
        shortcut: StandardKey.Open;
    }

    Action
    {
        id: showEngineLogAction;
        text: catalog.i18nc("@action:inmenu menubar:help","Show Engine &Log...");
        iconName: "view-list-text";
        shortcut: StandardKey.WhatsThis;
    }

    Action
    {
        id: configureSettingVisibilityAction
        text: catalog.i18nc("@action:menu", "Configure setting visiblity...");
        iconName: "configure"
    }
}
