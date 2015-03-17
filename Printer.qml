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

                MenuItem { action: actions.open; }
                MenuItem { action: actions.save; }

                MenuSeparator { }

                MenuItem { action: actions.quit; }
            }

            Menu {
                //: Edit menu
                title: qsTr("&Edit");

                MenuItem { action: actions.undo; }
                MenuItem { action: actions.redo; }
                MenuSeparator { }
                MenuItem { action: actions.deleteSelection; }
                MenuItem { action: actions.deleteAll; }
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


                MenuItem { action: actions.addMachine; }
                MenuItem { action: actions.settings; }
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

                MenuItem { action: actions.preferences; }
            }

            Menu {
                //: Help menu
                title: qsTr("&Help");

                MenuItem { action: actions.help; }
                MenuItem { action: actions.about; }
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

                undo: actions.undo;
                redo: actions.redo;
                settings: actions.settings;
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

                onRequestOpenFile: actions.open.trigger();
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

                onSaveRequested: actions.save.trigger();
                onSaveToSDRequested: Printer.saveToSD()
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

    UM.PreferencesDialog {
        id: preferences

        Component.onCompleted: {
            insertPage(1, qsTr('View'), Qt.resolvedUrl('./ViewPage.qml'));
        }
    }

    PrinterActions {
        id: actions;

        open.onTriggered: openDialog.open();
        save.onTriggered: saveDialog.open();

        quit.onTriggered: base.visible = false;

        undo.onTriggered: UM.OperationStack.undo();
        undo.enabled: UM.OperationStack.canUndo;
        redo.onTriggered: UM.OperationStack.redo();
        redo.enabled: UM.OperationStack.canRedo;

        deleteSelection.onTriggered: UM.Controller.removeSelection();

        addMachine.onTriggered: addMachine.visible = true;

        preferences.onTriggered: preferences.visible = true;
        settings.onTriggered: { preferences.visible = true; preferences.setPage(1); }
    }

    Menu {
        id: objectContextMenu;

        property variant id: -1;

        MenuItem { action: actions.centerObject; }
        MenuItem { action: actions.deleteObject; }
        MenuItem { action: actions.multiplyObject; }
        MenuItem { action: actions.splitObject; }
        MenuSeparator { }
        MenuItem { action: actions.deleteAll; }
        MenuItem { action: actions.reloadAll; }
        MenuItem { action: actions.resetAllTranslation; }
        MenuItem { action: actions.resetAll; }
    }

    Menu {
        id: contextMenu;

        MenuItem { action: actions.deleteAll; }
        MenuItem { action: actions.reloadAll; }
        MenuItem { action: actions.resetAllTranslation; }
        MenuItem { action: actions.resetAll; }
    }

    Connections {
        target: UM.Controller
        onContextMenuRequested: {
            if(id == 0) {
                contextMenu.popup();
            } else {
                objectContextMenu.id = id;
                objectContextMenu.popup();
            }
        }
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
            UM.MeshFileHandler.readLocalFile(fileUrl)
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
            UM.MeshFileHandler.writeLocalFile(fileUrl);
        }
    }

    AddMachineWizard {
        id: addMachine;
    }

    Connections {
        target: Printer
        onRequestAddPrinter: addMachine.visible = true;
    }
}
