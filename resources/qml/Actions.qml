// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import UM 1.1 as UM

Item
{
    property alias open: openAction;
    property alias save: saveAction;
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
    property alias splitObject: splitObjectAction;

    property alias deleteAll: deleteAllAction;
    property alias reloadAll: reloadAllAction;
    property alias resetAllTranslation: resetAllTranslationAction;
    property alias resetAll: resetAllAction;

    property alias addMachine: addMachineAction;
    property alias configureMachines: settingsAction;
    property alias manageProfiles: manageProfilesAction;

    property alias preferences: preferencesAction;

    property alias showEngineLog: showEngineLogAction;
    property alias documentation: documentationAction;
    property alias reportBug: reportBugAction;
    property alias about: aboutAction;

    property alias toggleFullScreen: toggleFullScreenAction;

    UM.I18nCatalog{id: catalog; name:"cura"}

    Action
    {
        id:toggleFullScreenAction
        shortcut: StandardKey.FullScreen;
        text: catalog.i18nc("@action","Toggle Full Screen");
    }

    Action
    {
        id: undoAction;
        text: catalog.i18nc("@action","Undo");
        iconName: "edit-undo";
        shortcut: StandardKey.Undo;
    }

    Action
    {
        id: redoAction;
        text: catalog.i18nc("@action","Redo");
        iconName: "edit-redo";
        shortcut: StandardKey.Redo;
    }

    Action
    {
        id: quitAction;
        text: catalog.i18nc("@action","Quit");
        iconName: "application-exit";
        shortcut: StandardKey.Quit;
    }

    Action
    {
        id: preferencesAction;
        text: catalog.i18nc("@action","Preferences...");
        iconName: "configure";
    }

    Action
    {
        id: addMachineAction;
        text: catalog.i18nc("@action","Add Printer...");
    }

    Action
    {
        id: settingsAction;
        text: catalog.i18nc("@action","Configure Printers");
        iconName: "configure";
    }

    Action
    {
        id: manageProfilesAction;
        text: catalog.i18nc("@action","Manage Profiles");
    }

    Action
    {
        id: documentationAction;
        text: catalog.i18nc("@action","Show Online &Documentation");
        iconName: "help-contents";
        shortcut: StandardKey.Help;
    }

    Action {
        id: reportBugAction;
        text: catalog.i18nc("@action","Report a &Bug");
        iconName: "tools-report-bug";
    }

    Action
    {
        id: aboutAction;
        text: catalog.i18nc("@action","About...");
        iconName: "help-about";
    }

    Action
    {
        id: deleteSelectionAction;
        text: catalog.i18nc("@action","Delete Selection");
        iconName: "edit-delete";
        shortcut: StandardKey.Delete;
    }

    Action
    {
        id: deleteObjectAction;
        text: catalog.i18nc("@action","Delete Object");
        iconName: "edit-delete";
        shortcut: StandardKey.Backspace;
    }

    Action
    {
        id: centerObjectAction;
        text: catalog.i18nc("@action","Center Object on Platform");
    }

    Action
    {
        id: groupObjectsAction
        text: catalog.i18nc("@action","Group objects");
        enabled: UM.Scene.numObjectsSelected > 1 ? true: false
    }

    Action
    {
        id: unGroupObjectsAction
        text: catalog.i18nc("@action","Ungroup objects");
        enabled: UM.Scene.isGroupSelected
    }
    
    Action
    {
        id: mergeObjectsAction
        text: catalog.i18nc("@action","Merge objects");
        enabled: UM.Scene.numObjectsSelected > 1 ? true: false
    }

    Action
    {
        id: multiplyObjectAction;
        text: catalog.i18nc("@action","Duplicate Object");
    }

    Action
    {
        id: splitObjectAction;
        text: catalog.i18nc("@action","Split Object into Parts");
        enabled: false;
    }

    Action
    {
        id: deleteAllAction;
        text: catalog.i18nc("@action","Clear Build Platform");
        iconName: "edit-clear";
    }

    Action
    {
        id: reloadAllAction;
        text: catalog.i18nc("@action","Reload All Objects");
    }

    Action
    {
        id: resetAllTranslationAction;
        text: catalog.i18nc("@action","Reset All Object Positions");
    }

    Action
    {
        id: resetAllAction;
        text: catalog.i18nc("@action","Reset All Object Transformations");
    }

    Action
    {
        id: openAction;
        text: catalog.i18nc("@action","Load file");
        iconName: "document-open";
        shortcut: StandardKey.Open;
    }

    Action
    {
        id: saveAction;
        text: catalog.i18nc("@action","Save...");
        iconName: "document-save";
        shortcut: StandardKey.Save;
    }

    Action
    {
        id: showEngineLogAction;
        text: catalog.i18nc("@action","Show engine &log...");
        iconName: "view-list-text";
    }
}
