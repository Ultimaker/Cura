// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1
import QtQuick.Dialogs 1.1

import UM 1.1 as UM

UM.MainWindow {
    id: base
    visible: true

    //: Cura application window title
    title: qsTr("Cura");

    Item {
        id: backgroundItem;
        anchors.fill: parent;

        UM.ApplicationMenu {
            id: menu
            window: base

            Menu {
                id: fileMenu
                //: File menu
                title: qsTr("&File");

                MenuItem { action: actions.open; }

                Menu {
                    id: recentFilesMenu;
                    title: "Open Recent"
                    iconName: "document-open-recent";

                    enabled: Printer.recentFiles.length > 0;

                    Instantiator {
                        model: Printer.recentFiles
                        MenuItem {
                            text: {
                                var path = modelData.toString()
                                return (index + 1) + ". " + path.slice(path.lastIndexOf("/") + 1);
                            }
                            onTriggered: UM.MeshFileHandler.readLocalFile(modelData);
                        }
                        onObjectAdded: recentFilesMenu.insertItem(index, object)
                        onObjectRemoved: recentFilesMenu.removeItem(object)
                    }
                }

                MenuSeparator { }

                MenuItem {
                    text: "Save Selection to File";
                    enabled: UM.Selection.hasSelection;
                    iconName: "document-save-as";
                    onTriggered: UM.OutputDeviceManager.requestWriteSelectionToDevice("local_file");
                }
                Menu {
                    id: saveAllMenu
                    title: "Save All"
                    iconName: "document-save";
                    enabled: devicesModel.count > 0 && UM.Backend.progress > 0.99;

                    Instantiator {
                        model: UM.OutputDevicesModel { id: devicesModel; }

                        MenuItem {
                            text: model.description;
                            onTriggered: UM.OutputDeviceManager.requestWriteToDevice(model.id);
                        }
                        onObjectAdded: saveAllMenu.insertItem(index, object)
                        onObjectRemoved: saveAllMenu.removeItem(object)
                    }
                }

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
            Menu
            {
                title: qsTr("&View");
                id: top_view_menu
                Instantiator 
                {
                    model: UM.Models.viewModel
                    MenuItem 
                    {
                        text: model.name;
                        checkable: true;
                        checked: model.active;
                        exclusiveGroup: view_menu_top_group;
                        onTriggered: UM.Controller.setActiveView(model.id);
                    }
                    onObjectAdded: top_view_menu.insertItem(index, object)
                    onObjectRemoved: top_view_menu.removeItem(object)
                }
                ExclusiveGroup { id: view_menu_top_group; }
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
                id: extension_menu
                //: Extensions menu
                title: qsTr("E&xtensions");

                Instantiator 
                {
                    model: UM.Models.extensionModel

                    Menu
                    {
                        id: sub_menu
                        title: model.name;

                        Instantiator
                        {
                            model: actions
                            MenuItem
                            {
                                text: model.text
                                onTriggered: UM.Models.extensionModel.subMenuTriggered(name, model.text)
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

                MenuItem { action: actions.showEngineLog; }
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
                            UM.MeshFileHandler.readLocalFile(drop.urls[i]);
                        }
                    }
                }
            }

            UM.MessageStack {
                anchors {
                    horizontalCenter: parent.horizontalCenter
                    horizontalCenterOffset: -(UM.Theme.sizes.logo.width/ 2)
                    top: parent.verticalCenter;
                    bottom: parent.bottom;
                }
            }

            Loader
            {
                id: view_panel

                //anchors.left: parent.left;
                //anchors.right: parent.right;
                //anchors.bottom: parent.bottom
                anchors.top: viewModeButton.bottom
                anchors.topMargin: UM.Theme.sizes.default_margin.height;
                anchors.right: sidebar.left;
                anchors.rightMargin: UM.Theme.sizes.window_margin.width;
                //anchors.bottom: buttons.top;
                //anchors.bottomMargin: UM.Theme.sizes.default_margin.height;

                height: childrenRect.height;

                source: UM.ActiveView.valid ? UM.ActiveView.activeViewPanel : "";
            }

            Button {
                id: openFileButton;
                //style: UM.Backend.progress < 0 ? UM.Theme.styles.open_file_button : UM.Theme.styles.tool_button;
                style: UM.Theme.styles.open_file_button
                tooltip: '';
                anchors {
                    top: parent.top;
                    topMargin: UM.Theme.sizes.loadfile_margin.height
                    left: parent.left;
                    leftMargin: UM.Theme.sizes.loadfile_margin.width
                }
                action: actions.open;
            }

            Image {
                id: logo
                anchors {
                    left: parent.left
                    leftMargin: UM.Theme.sizes.default_margin.width;
                    bottom: parent.bottom
                    bottomMargin: UM.Theme.sizes.default_margin.height;
                }

                source: UM.Theme.images.logo;
                width: UM.Theme.sizes.logo.width;
                height: UM.Theme.sizes.logo.height;

                sourceSize.width: width;
                sourceSize.height: height;
            }

            Button {
                id: viewModeButton
                anchors {
                    top: parent.top;
                    right: sidebar.left;
                    rightMargin: UM.Theme.sizes.window_margin.width;
                }
                //: View Mode toolbar button
                text: qsTr("View Mode");
                iconSource: UM.Theme.icons.viewmode;

                style: UM.Theme.styles.tool_button;
                tooltip: '';
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

            Toolbar {
                id: toolbar;

                anchors {
                    horizontalCenter: parent.horizontalCenter
                    horizontalCenterOffset: -(UM.Theme.sizes.panel.width / 2)
                    top: parent.top;
                }
            }

            Sidebar {
                id: sidebar;

                anchors {
                    top: parent.top;
                    bottom: parent.bottom;
                    right: parent.right;
                }

                width: UM.Theme.sizes.panel.width;

                addMachineAction: actions.addMachine;
                configureMachinesAction: actions.configureMachines;
            }

            Rectangle {
                x: base.mouseX + UM.Theme.sizes.default_margin.width;
                y: base.mouseY + UM.Theme.sizes.default_margin.height;

                width: childrenRect.width;
                height: childrenRect.height;
                Label {
                    text: UM.ActiveTool.properties.Rotation != undefined ? "%1°".arg(UM.ActiveTool.properties.Rotation) : "";
                }

                visible: UM.ActiveTool.valid && UM.ActiveTool.properties.Rotation != undefined;
            }
        }
    }

    UM.PreferencesDialog {
        id: preferences

        Component.onCompleted: {
            //: View preferences page title
            insertPage(1, qsTr("View"), "view-preview", Qt.resolvedUrl("./ViewPage.qml"));
        }
    }

    Actions {
        id: actions;

        open.onTriggered: openDialog.open();
        save.onTriggered: saveDialog.open();

        quit.onTriggered: base.visible = false;

        undo.onTriggered: UM.OperationStack.undo();
        undo.enabled: UM.OperationStack.canUndo;
        redo.onTriggered: UM.OperationStack.redo();
        redo.enabled: UM.OperationStack.canRedo;

        deleteSelection.onTriggered: {
            if(objectContextMenu.objectId != 0) {
                Printer.deleteObject(objectContextMenu.objectId);
            }
        }

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
        
        groupObjects.onTriggered:
        {
            Printer.groupSelected()
        }
        
        unGroupObjects.onTriggered:
        {
            Printer.ungroupSelected()
        }
        
        mergeObjects.onTriggered:
        {
            Printer.mergeSelected()
        }

        deleteAll.onTriggered: Printer.deleteAll()
        resetAllTranslation.onTriggered: Printer.resetAllTranslation()
        resetAll.onTriggered: Printer.resetAll()
        reloadAll.onTriggered: Printer.reloadAll()

        addMachine.onTriggered: addMachineWizard.visible = true;

        preferences.onTriggered: preferences.visible = true;
        configureMachines.onTriggered: { preferences.visible = true; preferences.setPage(2); }

        documentation.onTriggered: CuraActions.openDocumentation();
        reportBug.onTriggered: CuraActions.openBugReportPage();
        showEngineLog.onTriggered: engineLog.visible = true;
        about.onTriggered: aboutDialog.visible = true;
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
        MenuItem { action: actions.groupObjects;}
        MenuItem { action: actions.unGroupObjects;}
        MenuItem { action: actions.mergeObjects;}
    }

    Menu {
        id: contextMenu;
        MenuItem { action: actions.deleteAll; }
        MenuItem { action: actions.reloadAll; }
        MenuItem { action: actions.resetAllTranslation; }
        MenuItem { action: actions.resetAll; }
        MenuItem { action: actions.groupObjects;}
        MenuItem { action: actions.unGroupObjects;}
        MenuItem { action: actions.mergeObjects;}
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

    EngineLog {
        id: engineLog;
    }

    AddMachineWizard {
        id: addMachineWizard
    }


    AboutDialog {
        id: aboutDialog
    }

    Connections {
        target: Printer
        onRequestAddPrinter: {
            addMachineWizard.visible = true
            addMachineWizard.printer = false
        }
    }

    Component.onCompleted: UM.Theme.load(UM.Resources.getPath(UM.Resources.ThemesLocation, "cura"))
}

