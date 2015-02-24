import QtQuick 2.2
import QtQuick.Controls 1.1

Item {
    property alias open: openAction;
    property alias save: saveAction;
    property alias quit: quitAction;

    property alias undo: undoAction;
    property alias redo: redoAction;

    property alias deleteSelection: deleteAction;
    property alias deleteAll: deleteAllAction;

    property alias addMachine: addMachineAction;
    property alias settings: settingsAction;

    property alias preferences: preferencesAction;
    property alias help: helpAction;
    property alias about: aboutAction;

    Action {
        id: undoAction;
        //: Undo action
        text: qsTr("Undo");
        iconName: "edit-undo";
        shortcut: StandardKey.Undo;
    }

    Action {
        id: redoAction;
        //: Redo action
        text: qsTr("Redo");
        iconName: "edit-redo";
        shortcut: StandardKey.Redo;
    }

    Action {
        id: quitAction;
        //: Quit action
        text: qsTr("Quit");
        iconName: "application-exit";
        shortcut: StandardKey.Quit;
    }

    Action {
        id: preferencesAction;
        //: Preferences action
        text: qsTr("Preferences");
        iconName: "configure";
    }

    Action {
        id: addMachineAction;
        //: Add a Machine action
        text: qsTr("Add Printer...");
    }

    Action {
        id: settingsAction;
        //: Manage Printers action
        text: qsTr("Configure Printers");
        iconName: "configure";
    }

    Action {
        id: helpAction;
        //: Show Manual action
        text: qsTr("Show Manual");
        iconName: "help-contents";
        shortcut: StandardKey.Help;
    }

    Action {
        id: aboutAction;
        //: About action
        text: qsTr("About...");
        iconName: "help-about";
    }

    Action {
        id: deleteAction;
        //: Delete selection action
        text: qsTr("Delete Selection");
        iconName: "edit-delete";
        shortcut: StandardKey.Delete;
    }

    Action {
        id: deleteAllAction;
        //: Clear build platform action
        text: qsTr("Clear Build Platform");
        iconName: "edit-clear";
    }

    Action {
        id: openAction;
        //: Open file action
        text: qsTr("Open...");
        iconName: "document-open";
        shortcut: StandardKey.Open;
    }

    Action {
        id: saveAction;
        //: Save file action
        text: qsTr("Save...");
        iconName: "document-save";
        shortcut: StandardKey.Save;
    }
}
