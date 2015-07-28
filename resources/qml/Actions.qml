// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import UM 1.0 as UM

Item {
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

    property alias preferences: preferencesAction;

    property alias showEngineLog: showEngineLogAction;
    property alias documentation: documentationAction;
    property alias reportBug: reportBugAction;
    property alias about: aboutAction;

    Action {
        id: undoAction;
        //: Undo action
        text: qsTr("&Undo");
        iconName: "edit-undo";
        shortcut: StandardKey.Undo;
    }

    Action {
        id: redoAction;
        //: Redo action
        text: qsTr("&Redo");
        iconName: "edit-redo";
        shortcut: StandardKey.Redo;
    }

    Action {
        id: quitAction;
        //: Quit action
        text: qsTr("&Quit");
        iconName: "application-exit";
        shortcut: StandardKey.Quit;
    }

    Action {
        id: preferencesAction;
        //: Preferences action
        text: qsTr("&Preferences...");
        iconName: "configure";
    }

    Action {
        id: addMachineAction;
        //: Add Printer action
        text: qsTr("&Add Printer...");
    }

    Action {
        id: settingsAction;
        //: Configure Printers action
        text: qsTr("&Configure Printers");
        iconName: "configure";
    }

    Action {
        id: documentationAction;
        //: Show Online Documentation action
        text: qsTr("Show Online &Documentation");
        iconName: "help-contents";
        shortcut: StandardKey.Help;
    }

    Action {
        id: reportBugAction;
        //: Report a Bug Action
        text: qsTr("Report a &Bug");
        iconName: "tools-report-bug";
    }

    Action {
        id: aboutAction;
        //: About action
        text: qsTr("&About...");
        iconName: "help-about";
    }

    Action {
        id: deleteSelectionAction;
        //: Delete selection action
        text: qsTr("Delete Selection");
        iconName: "edit-delete";
        shortcut: StandardKey.Delete;
    }

    Action {
        id: deleteObjectAction;
        //: Delete object action
        text: qsTr("Delete Object");
        iconName: "edit-delete";
    }

    Action {
        id: centerObjectAction;
        //: Center object action
        text: qsTr("Center Object on Platform");
    }
    
    Action
    {
        id: groupObjectsAction
        text: qsTr("Group objects");
        enabled: UM.Scene.numObjectsSelected > 1 ? true: false
    }

    Action
    {
        id: unGroupObjectsAction
        text: qsTr("Ungroup objects");
        enabled: UM.Scene.isGroupSelected
    }
    
    Action
    {
        id: mergeObjectsAction
        text: qsTr("Merge objects");
        enabled: UM.Scene.numObjectsSelected > 1 ? true: false
    }
    
    Action {
        id: multiplyObjectAction;
        //: Duplicate object action
        text: qsTr("Duplicate Object");
    }

    Action {
        id: splitObjectAction;
        //: Split object action
        text: qsTr("Split Object into Parts");
        enabled: false;
    }

    Action {
        id: deleteAllAction;
        //: Clear build platform action
        text: qsTr("Clear Build Platform");
        iconName: "edit-clear";
    }

    Action {
        id: reloadAllAction;
        //: Reload all objects action
        text: qsTr("Reload All Objects");
    }

    Action {
        id: resetAllTranslationAction;
        //: Reset all positions action
        text: qsTr("Reset All Object Positions");
    }

    Action {
        id: resetAllAction;
        //: Reset all positions action
        text: qsTr("Reset All Object Transformations");
    }

    Action {
        id: openAction;
        //: Open file action
        text: qsTr("&Open...");
        iconName: "document-open";
        shortcut: StandardKey.Open;
    }

    Action {
        id: saveAction;
        //: Save file action
        text: qsTr("&Save...");
        iconName: "document-save";
        shortcut: StandardKey.Save;
    }

    Action {
        id: showEngineLogAction;
        //: Show engine log action
        text: qsTr("Show engine &log...");
        iconName: "view-list-text";
    }
}
