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
    }

    Action
    {
        id: undoAction;
        //: Undo action
        text: catalog.i18nc("@action","Undo");
        iconName: "edit-undo";
        shortcut: StandardKey.Undo;
    }

    Action
    {
        id: redoAction;
        //: Redo action
        text: catalog.i18nc("@action","Redo");
        iconName: "edit-redo";
        shortcut: StandardKey.Redo;
    }

    Action
    {
        id: quitAction;
        //: Quit action
        text: catalog.i18nc("@action","Quit");
        iconName: "application-exit";
        shortcut: StandardKey.Quit;
    }

    Action
    {
        id: preferencesAction;
        //: Preferences action
        text: catalog.i18nc("@action","Preferences...");
        iconName: "configure";
    }

    Action
    {
        id: addMachineAction;
        //: Add Printer action
        text: catalog.i18nc("@action","Add Printer...");
    }

    Action
    {
        id: settingsAction;
        //: Configure Printers action
        text: catalog.i18nc("@action","Configure Printers");
        iconName: "configure";
    }

    Action
    {
        id: manageProfilesAction;
        //: manage profiles action
        text: catalog.i18nc("@action","Manage Profiles");
    }

    Action
    {
        id: documentationAction;
        //: Show Online Documentation action
        text: catalog.i18nc("@action","Show Online &Documentation");
        iconName: "help-contents";
        shortcut: StandardKey.Help;
    }

    Action {
        id: reportBugAction;
        //: Report a Bug Action
        text: catalog.i18nc("@action","Report a &Bug");
        iconName: "tools-report-bug";
    }

    Action
    {
        id: aboutAction;
        //: About action
        text: catalog.i18nc("@action","About...");
        iconName: "help-about";
    }

    Action
    {
        id: deleteSelectionAction;
        //: Delete selection action
        text: catalog.i18nc("@action","Delete Selection");
        iconName: "edit-delete";
        shortcut: StandardKey.Delete;
    }

    Action
    {
        id: deleteObjectAction;
        //: Delete object action
        text: catalog.i18nc("@action","Delete Object");
        iconName: "edit-delete";
        shortcut: StandardKey.Backspace;
    }

    Action
    {
        id: centerObjectAction;
        //: Center object action
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
        //: Duplicate object action
        text: catalog.i18nc("@action","Duplicate Object");
    }

    Action
    {
        id: splitObjectAction;
        //: Split object action
        text: catalog.i18nc("@action","Split Object into Parts");
        enabled: false;
    }

    Action
    {
        id: deleteAllAction;
        //: Clear build platform action
        text: catalog.i18nc("@action","Clear Build Platform");
        iconName: "edit-clear";
    }

    Action
    {
        id: reloadAllAction;
        //: Reload all objects action
        text: catalog.i18nc("@action","Reload All Objects");
    }

    Action
    {
        id: resetAllTranslationAction;
        //: Reset all positions action
        text: catalog.i18nc("@action","Reset All Object Positions");
    }

    Action
    {
        id: resetAllAction;
        //: Reset all positions action
        text: catalog.i18nc("@action","Reset All Object Transformations");
    }

    Action
    {
        id: openAction;
        //: Open file action
        text: catalog.i18nc("@action","Load file");
        iconName: "document-open";
        shortcut: StandardKey.Open;
    }

    Action
    {
        id: saveAction;
        //: Save file action
        text: catalog.i18nc("@action","Save...");
        iconName: "document-save";
        shortcut: StandardKey.Save;
    }

    Action
    {
        id: showEngineLogAction;
        //: Show engine log action
        text: catalog.i18nc("@action","Show engine &log...");
        iconName: "view-list-text";
    }
}
