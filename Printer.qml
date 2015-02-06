import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1
import QtQuick.Dialogs 1.1

import UM 1.0 as UM

UM.MainWindow {
    id: base
    visible: true

    width: 1280
    height: 720

    title: "Cura";

    Item {
        id: backgroundItem;
        anchors.fill: parent;

        UM.ApplicationMenu {
            id: menu
            window: base

            Menu {
                title: '&File';

                MenuItem { action: loadFileAction; }
                MenuItem { action: saveFileAction; }

                MenuSeparator { }

                MenuItem { action: quitAction; }
            }

            Menu {
                title: '&Edit';

                MenuItem { action: undoAction; }
                MenuItem { action: redoAction; }
                MenuSeparator { }
                MenuItem { action: deleteAction; }
                MenuItem { action: deleteAllAction; }
            }

            Menu {
                id: machineMenu;
                title: "&Machine";

                Instantiator {
                    model: UM.Models.machinesModel
                    MenuItem {
                        text: model.name;
                        checkable: true;
                        exclusiveGroup: machineMenuGroup;
                    }
                    onObjectAdded: machineMenu.insertItem(index, object)
                    onObjectRemoved: machineMenu.removeItem(object)
                }

                ExclusiveGroup { id: machineMenuGroup; }
                MenuSeparator { }
                MenuItem { text: "Add new machine..."; enabled: false; }
            }

            Menu {
                title: 'E&xtensions';

                MenuItem { text: "No extensions loaded"; enabled: false; }
            }

            Menu {
                title: '&Settings';

                MenuItem { action: preferencesAction; }
            }

            Menu {
                title: '&Help';

                MenuItem { action: helpAction; enabled: false; }
                MenuItem { action: aboutAction; enabled: false; }
            }
        }

        Item {
            id: contentItem;

            y: menu.height
            width: parent.width;
            height: parent.height - menu.height;

            Keys.forwardTo: menu

            DropArea {
                anchors.fill: parent;
                onDropped: {
                    if(drop.urls.length > 0) {
                        for(var i in drop.urls) {
                            UM.Controller.addMesh(drop.urls[i]);
                        }
                    }
                }
            }

            UM.Toolbar {
                id: toolbar;

                anchors {
                    left: parent.left;
                    right: parent.right;
                    top: parent.top;
                }

                undo: undoAction;
                redo: redoAction;
                settings: settingsAction;
            }

            FilePane {
                id: files;

                anchors.left: parent.left;
                anchors.leftMargin: UM.Theme.windowLeftMargin;
                anchors.top: toolbar.bottom;
                anchors.topMargin: -1;

                border.width: 1;
                border.color: UM.Theme.borderColor;

                width: UM.Theme.panelWidth;
                height: base.height / 2 - UM.Theme.toolbarHeight;

                onRequestOpenFile: openDialog.open();
                onOpenFile: UM.Controller.addMesh(file);
            }

            SettingsPane {
                id: settings;

                anchors.right: parent.right;
                anchors.rightMargin: UM.Theme.windowRightMargin;
                anchors.top: toolbar.bottom;
                anchors.topMargin: -1;

                border.width: 1;
                border.color: UM.Theme.borderColor;

                width: UM.Theme.panelWidth;

                expandedHeight: base.height;
            }

            OutputGCodeButton {
                anchors.right: parent.right;
                anchors.rightMargin: UM.Theme.windowRightMargin;

                anchors.bottom: parent.bottom;
                anchors.bottomMargin: -1;

                width: UM.Theme.panelWidth;
                height: 40;
            }

//             UM.JobList { anchors.left: parent.left; anchors.bottom: parent.bottom; width: parent.width / 10; height: parent.height / 5; }

//             ProgressBar {
//                 id: progressBar;
//
//                 anchors {
//                     left: parent.left;
//                     bottom: parent.bottom;
//                     right: parent.right;
//                 }
//
//                 minimumValue: 0;
//                 maximumValue: 1;
//
//                 Connections {
//                     target: UM.Backend;
//                     onProcessingProgress: progressBar.value = amount;
//                 }
//             }
        }
    }

    UM.PreferencesDialog { id: preferences }

    Action {
        id: undoAction;
        text: "Undo";
        iconName: "edit-undo";
        shortcut: StandardKey.Undo;
        onTriggered: UM.OperationStack.undo();
        enabled: UM.OperationStack.canUndo;
    }

    Action {
        id: redoAction;
        text: "Redo";
        iconName: "edit-redo";
        shortcut: StandardKey.Redo;
        onTriggered: UM.OperationStack.redo();
        enabled: UM.OperationStack.canRedo;
    }

    Action {
        id: quitAction;
        text: "Quit";
        iconName: "application-exit";
        shortcut: StandardKey.Quit;
        onTriggered: Qt.quit();
    }

    Action {
        id: preferencesAction;
        text: "Preferences";
        iconName: "configure";
        onTriggered: preferences.visible = true;
    }

    Action {
        id: settingsAction;
        text: "Configure Printers";
        iconSource: UM.Resources.getIcon("settings.png");
        onTriggered: preferences.visible = true;
    }

    Action {
        id: helpAction;
        text: "Show Manual";
        iconName: "help-contents";
        shortcut: StandardKey.Help;
    }

    Action {
        id: aboutAction;
        text: "About...";
        iconName: "help-about";
    }

    Action {
        id: deleteAction;
        text: "Delete Selection";
        iconName: "edit-delete";
        shortcut: StandardKey.Delete;
        onTriggered: UM.Controller.removeSelection();
    }

    Action {
        id: deleteAllAction;
        text: "Clear Build Platform";
        iconName: "edit-clear";
        enabled: false;
    }

    Action {
        id: loadFileAction;
        text: "Open...";
        iconName: "document-open";
        shortcut: StandardKey.Open;
        onTriggered: openDialog.open();
    }

    Action {
        id: saveFileAction;
        text: "Save...";
        iconName: "document-save";
        shortcut: StandardKey.Save;
        enabled: false;
    }

    Menu {
        id: contextMenu;

        MenuItem { action: deleteAction; }
    }

    FileDialog {
        id: openDialog;

        title: "Choose files"
        modality: Qt.NonModal
        //TODO: Support multiple file selection, workaround bug in KDE file dialog
        //selectMultiple: true

        onAccepted:
        {
            UM.Controller.addMesh(fileUrl)
            files.setDirectory(fileUrl)
        }
    }

    FileDialog {
        id: saveDialog;
        title: "Choose Filename";
        selectExisting: false;

        onAccepted:
        {
            Printer.saveGCode(fileUrl);
        }
    }
}
