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
                MenuItem { action: actions.configureMachines; }
            }

            Menu {
                id:extension_menu
                //: Extensions menu
                title: qsTr("E&xtensions");

                Instantiator 
                {
                    model: UM.Models.extensionModel
                    id: blub
                    
                    Menu
                    {
                        title: model.name;
                        id: sub_menu
                        Instantiator
                        {
                            model: actions
                            MenuItem 
                            {
                                text:model.text
                                onTriggered: UM.Models.extensionModel.subMenuTriggered(name,model.text)
                            }
                            onObjectAdded: sub_menu.insertItem(index, object)
                            onObjectRemoved: sub_menu.removeItem(object)
                            
                        }
       
                    }
                    onObjectAdded: extension_menu.insertItem(index, object)
                    onObjectRemoved: extension_menu.removeItem(object)
                }
            }

            Menu {
                //: Settings menu
                title: qsTr("&Settings");

                MenuItem { action: actions.preferences; }
            }

            Menu {
                //: Help menu
                title: qsTr("&Help");

                MenuItem { action: actions.documentation; }
                MenuItem { action: actions.reportBug; }
                MenuSeparator { }
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

            UM.Sidebar {
                id: sidebar;

                anchors {
                    top: parent.top;
                    bottom: parent.bottom;
                    right: parent.right;
                    rightMargin: UM.Theme.sizes.window_margin.width;
                }

                width: UM.Theme.sizes.panel.width;

                addMachineAction: actions.addMachine;
                configureMachinesAction: actions.configureMachines;
                saveAction: actions.save;
            }

            UM.MessageStack {
                anchors.bottom: parent.bottom;
                anchors.horizontalCenter: parent.horizontalCenter;
                width: parent.width * 0.333;
                height: 250;
            }

            DescriptionPane {
                id: descriptionPane;
                anchors.right: sidebar.left;
            }

            PrinterButton {
                id: openFileButton;

                iconSource: UM.Theme.icons.open;

                anchors {
                    top: parent.top;
                    topMargin: UM.Theme.sizes.window_margin.height;
                    left: parent.left;
                    leftMargin: UM.Theme.sizes.window_margin.width;
                }

                action: actions.open;
            }

            Image {
                anchors {
                    verticalCenter: openFileButton.verticalCenter;
                    left: openFileButton.right;
                    leftMargin: UM.Theme.sizes.window_margin.width;
                }

                source: UM.Theme.images.logo;
                width: UM.Theme.sizes.logo.width;
                height: UM.Theme.sizes.logo.height;

                sourceSize.width: width;
                sourceSize.height: height;
            }

            PrinterButton {
                anchors {
                    top: parent.top;
                    topMargin: UM.Theme.sizes.window_margin.height;
                    right: sidebar.left;
                    rightMargin: UM.Theme.sizes.window_margin.width;
                }

                //: View Mode toolbar button
                text: qsTr("View Mode");
                iconSource: UM.Theme.icons.viewmode;

                menu: Menu {
                    id: viewMenu;
                    Instantiator {
                        model: UM.Models.viewModel;
                        MenuItem {
                            text: model.name;
                            checkable: true;
                            checked: model.active;
                            exclusiveGroup: viewMenuGroup;
                            onTriggered: UM.Controller.setActiveView(model.id);
                        }
                        onObjectAdded: viewMenu.insertItem(index, object)
                        onObjectRemoved: viewMenu.removeItem(object)
                    }

                    ExclusiveGroup { id: viewMenuGroup; }
                }
            }

            PrinterToolbar {
                anchors {
                    left: parent.left;
                    leftMargin: UM.Theme.sizes.window_margin.width;
                    bottom: parent.bottom;
                    bottomMargin: UM.Theme.sizes.window_margin.height;
                }
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

        deleteObject.onTriggered: {
            if(objectContextMenu.objectId != 0) {
                Printer.deleteObject(objectContextMenu.objectId);
                objectContextMenu.objectId = 0;
            }
        }

        multiplyObject.onTriggered: {
            if(objectContextMenu.objectId != 0) {
                Printer.multiplyObject(objectContextMenu.objectId, 1);
                objectContextMenu.objectId = 0;
            }
        }

        centerObject.onTriggered: {
            if(objectContextMenu.objectId != 0) {
                Printer.centerObject(objectContextMenu.objectId);
                objectContextMenu.objectId = 0;
            }
        }

        deleteAll.onTriggered: Printer.deleteAll()
        resetAllTranslation.onTriggered: Printer.resetAllTranslation()
        resetAll.onTriggered: Printer.resetAll()
        reloadAll.onTriggered: Printer.reloadAll()

        addMachine.onTriggered: addMachine.visible = true;

        preferences.onTriggered: preferences.visible = true;
        configureMachines.onTriggered: { preferences.visible = true; preferences.setPage(2); }

        documentation.onTriggered: Qt.openUrlExternally("https://ultimaker.com/en/support");
        reportBug.onTriggered: Qt.openUrlExternally("https://github.com/Ultimaker/PluggableCura/issues");
    }

    Menu {
        id: objectContextMenu;

        property variant objectId: -1;

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
            if(objectId == 0) {
                contextMenu.popup();
            } else {
                objectContextMenu.objectId = objectId;
                objectContextMenu.popup();
            }
        }
    }

    FileDialog {
        id: openDialog;

        //: File open dialog title
        title: qsTr("Open File")
        modality: UM.Application.platform == "linux" ? Qt.NonModal : Qt.WindowModal;
        //TODO: Support multiple file selection, workaround bug in KDE file dialog
        //selectMultiple: true

        nameFilters: UM.MeshFileHandler.supportedReadFileTypes;

        onAccepted:
        {
            UM.MeshFileHandler.readLocalFile(fileUrl)
        }
    }

    FileDialog {
        id: saveDialog;
        //: File save dialog title
        title: qsTr("Save File");
        selectExisting: false;

        modality: UM.Application.platform == "linux" ? Qt.NonModal : Qt.WindowModal;

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
        onWriteToLocalFileRequested: saveDialog.open();
    }

    Component.onCompleted: UM.Theme.load(UM.Resources.getPath(UM.Resources.ThemesLocation, "cura"))
}
