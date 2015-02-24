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

    title: qsTr("Cura");

    Item {
        id: backgroundItem;
        anchors.fill: parent;

        UM.ApplicationMenu {
            id: menu
            window: base

            Menu {
                //: File menu
                title: qsTr("&File");

                MenuItem { action: openAction; }
                MenuItem { action: saveAction; }

                MenuSeparator { }

                MenuItem { action: quitAction; }
            }

            Menu {
                //: Edit menu
                title: qsTr("&Edit");

                MenuItem { action: undoAction; }
                MenuItem { action: redoAction; }
                MenuSeparator { }
                MenuItem { action: deleteAction; }
                MenuItem { action: deleteAllAction; }
            }

            Menu {
                id: machineMenu;
                //: Machine menu
                title: qsTr("&Machine");

                Instantiator {
                    model: UM.Models.machinesModel
                    MenuItem {
                        text: model.name;
                        checkable: true;
                        checked: model.active;
                        exclusiveGroup: machineMenuGroup;
                        onTriggered: UM.Models.machinesModel.setActive(index)
                    }
                    onObjectAdded: machineMenu.insertItem(index, object)
                    onObjectRemoved: machineMenu.removeItem(object)
                }

                ExclusiveGroup { id: machineMenuGroup; }

                MenuSeparator { }


                MenuItem { action: addMachineAction; }
                MenuItem { action: settingsAction; }
            }

            Menu {
                //: Extensions menu
                title: qsTr("E&xtensions");

                //: Empty extensions menu
                MenuItem { text: qsTr("No extensions loaded"); enabled: false; }
            }

            Menu {
                //: Settings menu
                title: qsTr("&Settings");

                MenuItem { action: preferencesAction; }
            }

            Menu {
                //: Help menu
                title: qsTr("&Help");

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

            PrinterToolbar {
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

                onRequestOpenFile: openAction.trigger();
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

                onShowDescription: {
                    descriptionPane.show(text, x, y - contentItem.y);
                }
            }

            OutputGCodeButton {
                anchors.right: parent.right;
                anchors.rightMargin: UM.Theme.windowRightMargin;

                anchors.bottom: parent.bottom;
                anchors.bottomMargin: -1;

                width: UM.Theme.panelWidth;
                height: 40;

                onSaveRequested: saveAction.trigger();
            }

            UM.MessageStack {
                anchors.bottom: parent.bottom;
                anchors.horizontalCenter: parent.horizontalCenter;
                width: parent.width * 0.333;
                height: 250;
            }

            DescriptionPane {
                id: descriptionPane;
                anchors.right: settings.left;
            }
        }
    }

    UM.PreferencesDialog { id: preferences }

    Action {
        id: undoAction;
        //: Undo action
        text: qsTr("Undo");
        iconName: "edit-undo";
        shortcut: StandardKey.Undo;
        onTriggered: UM.OperationStack.undo();
        enabled: UM.OperationStack.canUndo;
    }

    Action {
        id: redoAction;
        //: Redo action
        text: qsTr("Redo");
        iconName: "edit-redo";
        shortcut: StandardKey.Redo;
        onTriggered: UM.OperationStack.redo();
        enabled: UM.OperationStack.canRedo;
    }

    Action {
        id: quitAction;
        //: Quit action
        text: qsTr("Quit");
        iconName: "application-exit";
        shortcut: StandardKey.Quit;
        onTriggered: base.visible = false;
    }

    Action {
        id: preferencesAction;
        //: Preferences action
        text: qsTr("Preferences");
        iconName: "configure";
        onTriggered: preferences.visible = true;
    }

    Action {
        id: settingsAction;
        //: Manage Printers action
        text: qsTr("Configure Printers");
        iconSource: UM.Resources.getIcon("settings.png");
        onTriggered: preferences.visible = true;
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
        onTriggered: UM.Controller.removeSelection();
    }

    Action {
        id: deleteAllAction;
        //: Clear build platform action
        text: qsTr("Clear Build Platform");
        iconName: "edit-clear";
        enabled: false;
    }

    Action {
        id: openAction;
        //: Open file action
        text: qsTr("Open...");
        iconName: "document-open";
        shortcut: StandardKey.Open;
        onTriggered: openDialog.open();
    }

    Action {
        id: saveAction;
        //: Save file action
        text: qsTr("Save...");
        iconName: "document-save";
        shortcut: StandardKey.Save;
        onTriggered: saveDialog.open();
    }

    Menu {
        id: contextMenu;

        MenuItem { action: deleteAction; }
    }

    FileDialog {
        id: openDialog;

        //: File open dialog title
        title: qsTr("Open File")
        modality: UM.Application.platform == "linux" ? Qt.NonModal : Qt.Modal;
        //TODO: Support multiple file selection, workaround bug in KDE file dialog
        //selectMultiple: true

        nameFilters: UM.MeshFileHandler.supportedReadFileTypes;

        onAccepted:
        {
            UM.Controller.addMesh(fileUrl)
            files.setDirectory(fileUrl)
        }
    }

    FileDialog {
        id: saveDialog;
        //: File save dialog title
        title: qsTr("Save File");
        selectExisting: false;

        modality: UM.Application.platform == "linux" ? Qt.NonModal : Qt.Modal;

        nameFilters: UM.MeshFileHandler.supportedWriteFileTypes

        onAccepted:
        {
            Printer.saveGCode(fileUrl);
        }
    }
}
