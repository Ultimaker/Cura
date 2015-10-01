// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1
import QtQuick.Dialogs 1.1

import UM 1.1 as UM

UM.MainWindow
{
    id: base
    //: Cura application window title
    title: catalog.i18nc("@title:window","Cura");

    viewportRect: Qt.rect(0, 0, (base.width - sidebar.width) / base.width, 1.0)

    Item
    {
        id: backgroundItem;
        anchors.fill: parent;
        UM.I18nCatalog{id: catalog; name:"cura"}
        UM.ApplicationMenu
        {
            id: menu
            window: base

            Menu
            {
                id: fileMenu
                //: File menu
                title: catalog.i18nc("@title:menu","&File");

                MenuItem {
                    action: actions.open;
                }

                Menu
                {
                    id: recentFilesMenu;
                    title: catalog.i18nc("@title:menu", "Open &Recent")
                    iconName: "document-open-recent";

                    enabled: Printer.recentFiles.length > 0;

                    Instantiator
                    {
                        model: Printer.recentFiles
                        MenuItem
                        {
                            text:
                            {
                                var path = modelData.toString()
                                return (index + 1) + ". " + path.slice(path.lastIndexOf("/") + 1);
                            }
                            onTriggered: {
                                UM.MeshFileHandler.readLocalFile(modelData);
                                openDialog.sendMeshName(modelData.toString())
                            }
                        }
                        onObjectAdded: recentFilesMenu.insertItem(index, object)
                        onObjectRemoved: recentFilesMenu.removeItem(object)
                    }
                }

                MenuSeparator { }

                MenuItem
                {
                    text: catalog.i18nc("@action:inmenu", "&Save Selection to File");
                    enabled: UM.Selection.hasSelection;
                    iconName: "document-save-as";
                    onTriggered: UM.OutputDeviceManager.requestWriteSelectionToDevice("local_file", Printer.jobName);
                }
                Menu
                {
                    id: saveAllMenu
                    title: catalog.i18nc("@title:menu","Save &All")
                    iconName: "document-save-all";
                    enabled: devicesModel.rowCount() > 0 && UM.Backend.progress > 0.99;

                    Instantiator
                    {
                        model: UM.OutputDevicesModel { id: devicesModel; }

                        MenuItem
                        {
                            text: model.description;
                            onTriggered: UM.OutputDeviceManager.requestWriteToDevice(model.id, Printer.jobName);
                        }
                        onObjectAdded: saveAllMenu.insertItem(index, object)
                        onObjectRemoved: saveAllMenu.removeItem(object)
                    }
                }

                MenuItem { action: actions.reloadAll; }

                MenuSeparator { }

                MenuItem { action: actions.quit; }
            }

            Menu
            {
                //: Edit menu
                title: catalog.i18nc("@title:menu","&Edit");

                MenuItem { action: actions.undo; }
                MenuItem { action: actions.redo; }
                MenuSeparator { }
                MenuItem { action: actions.deleteSelection; }
                MenuItem { action: actions.deleteAll; }
                MenuItem { action: actions.resetAllTranslation; }
                MenuItem { action: actions.resetAll; }
                MenuSeparator { }
                MenuItem { action: actions.groupObjects;}
                MenuItem { action: actions.mergeObjects;}
                MenuItem { action: actions.unGroupObjects;}
            }

            Menu
            {
                title: catalog.i18nc("@title:menu","&View");
                id: top_view_menu
                Instantiator 
                {
                    model: UM.ViewModel { }
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

                MenuSeparator { }

                MenuItem { action: actions.toggleFullScreen; }
            }
            Menu
            {
                id: machineMenu;
                //: Machine menu
                title: catalog.i18nc("@title:menu","&Machine");

                Instantiator
                {
                    model: UM.MachineInstancesModel { }
                    MenuItem
                    {
                        text: model.name;
                        checkable: true;
                        checked: model.active;
                        exclusiveGroup: machineMenuGroup;
                        onTriggered: UM.MachineManager.setActiveMachineInstance(model.name)
                    }
                    onObjectAdded: machineMenu.insertItem(index, object)
                    onObjectRemoved: machineMenu.removeItem(object)
                }

                ExclusiveGroup { id: machineMenuGroup; }

                MenuSeparator { }

                Instantiator
                {
                    model: UM.MachineVariantsModel { }
                    MenuItem {
                        text: model.name;
                        checkable: true;
                        checked: model.active;
                        exclusiveGroup: machineVariantsGroup;
                        onTriggered: UM.MachineManager.setActiveMachineVariant(model.name)
                    }
                    onObjectAdded: machineMenu.insertItem(index, object)
                    onObjectRemoved: machineMenu.removeItem(object)
                }

                ExclusiveGroup { id: machineVariantsGroup; }

                MenuSeparator { visible: UM.MachineManager.hasVariants; }

                MenuItem { action: actions.addMachine; }
                MenuItem { action: actions.configureMachines; }
            }

            Menu
            {
                id: profileMenu
                title: catalog.i18nc("@title:menu", "&Profile")

                Instantiator
                {
                    model: UM.ProfilesModel { }
                    MenuItem {
                        text: model.name;
                        checkable: true;
                        checked: model.active;
                        exclusiveGroup: profileMenuGroup;
                        onTriggered: UM.MachineManager.setActiveProfile(model.name)
                    }
                    onObjectAdded: profileMenu.insertItem(index, object)
                    onObjectRemoved: profileMenu.removeItem(object)
                }

                ExclusiveGroup { id: profileMenuGroup; }

                MenuSeparator { }

                MenuItem { action: actions.manageProfiles; }
            }

            Menu
            {
                id: extension_menu
                //: Extensions menu
                title: catalog.i18nc("@title:menu","E&xtensions");

                Instantiator 
                {
                    model: UM.Models.extensionModel

                    Menu
                    {
                        id: sub_menu
                        title: model.name;
                        visible: actions != null
                        enabled:actions != null
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

            Menu
            {
                //: Settings menu
                title: catalog.i18nc("@title:menu","&Settings");

                MenuItem { action: actions.preferences; }
            }

            Menu
            {
                //: Help menu
                title: catalog.i18nc("@title:menu","&Help");

                MenuItem { action: actions.showEngineLog; }
                MenuItem { action: actions.documentation; }
                MenuItem { action: actions.reportBug; }
                MenuSeparator { }
                MenuItem { action: actions.about; }
            }
        }

        Item
        {
            id: contentItem;

            y: menu.height
            width: parent.width;
            height: parent.height - menu.height;

            Keys.forwardTo: menu

            DropArea
            {
                anchors.fill: parent;
                onDropped:
                {
                    if(drop.urls.length > 0)
                    {
                        for(var i in drop.urls)
                        {
                            UM.MeshFileHandler.readLocalFile(drop.urls[i]);
                            if (i == drop.urls.length - 1)
                            {
                                openDialog.sendMeshName(drop.urls[i].toString())
                            }
                        }
                    }
                }
            }

            UM.MessageStack
            {
                anchors
                {
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

            Button
            {
                id: openFileButton;
                //style: UM.Backend.progress < 0 ? UM.Theme.styles.open_file_button : UM.Theme.styles.tool_button;
                //style: UM.Theme.styles.open_file_button
                text: catalog.i18nc("@action:button","Open File");
                iconSource: UM.Theme.icons.load
                style: UM.Theme.styles.open_file_button
                tooltip: '';
                anchors
                {
                    top: parent.top;
                    //topMargin: UM.Theme.sizes.loadfile_margin.height
                    left: parent.left;
                    //leftMargin: UM.Theme.sizes.loadfile_margin.width
                }
                action: actions.open;
            }

            Image
            {
                id: logo
                anchors
                {
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

            Button
            {
                id: viewModeButton
                property bool verticalTooltip: true

                anchors
                {
                    top: parent.top;
                    right: sidebar.left;
                    rightMargin: UM.Theme.sizes.window_margin.width;
                }
                text: catalog.i18nc("@action:button","View Mode");
                iconSource: UM.Theme.icons.viewmode;

                style: UM.Theme.styles.tool_button;
                tooltip: '';
                menu: Menu
                {
                    id: viewMenu;
                    Instantiator
                    {
                        id: viewMenuInstantiator
                        model: UM.ViewModel { }
                        MenuItem
                        {
                            text: model.name
                            checkable: true;
                            checked: model.active
                            exclusiveGroup: viewMenuGroup;
                            onTriggered: UM.Controller.setActiveView(model.id);
                        }
                        onObjectAdded: viewMenu.insertItem(index, object)
                        onObjectRemoved: viewMenu.removeItem(object)
                    }

                    ExclusiveGroup { id: viewMenuGroup; }
                }
            }

            Toolbar
            {
                id: toolbar;

                anchors {
                    left: parent.left
                    top: parent.top
                    topMargin: UM.Theme.sizes.window_margin.height + UM.Theme.sizes.button.height
                    //horizontalCenter: parent.horizontalCenter
                    //horizontalCenterOffset: -(UM.Theme.sizes.sidebar.width / 2)
                    //top: parent.top;
                }
            }

            Sidebar
            {
                id: sidebar;

                anchors
                {
                    top: parent.top;
                    bottom: parent.bottom;
                    right: parent.right;
                }

                width: UM.Theme.sizes.sidebar.width;

                addMachineAction: actions.addMachine;
                configureMachinesAction: actions.configureMachines;
                manageProfilesAction: actions.manageProfiles;
            }

            Rectangle
            {
                x: base.mouseX + UM.Theme.sizes.default_margin.width;
                y: base.mouseY + UM.Theme.sizes.default_margin.height;

                width: childrenRect.width;
                height: childrenRect.height;
                Label
                {
                    text: UM.ActiveTool.properties.Rotation != undefined ? "%1°".arg(UM.ActiveTool.properties.Rotation) : "";
                }

                visible: UM.ActiveTool.valid && UM.ActiveTool.properties.Rotation != undefined;
            }
        }
    }

    UM.PreferencesDialog
    {
        id: preferences

        Component.onCompleted:
        {
            //; Remove & re-add the general page as we want to use our own instead of uranium standard.
            removePage(0);
            insertPage(0, catalog.i18nc("@title:tab","General") , "" , Qt.resolvedUrl("./GeneralPage.qml"));

            //: View preferences page title
            insertPage(1, catalog.i18nc("@title:tab","View"), "view-preview", Qt.resolvedUrl("./ViewPage.qml"));

            //Force refresh
            setPage(0)
        }
    }

    Actions
    {
        id: actions;

        open.onTriggered: openDialog.open();

        quit.onTriggered: base.visible = false;

        undo.onTriggered: UM.OperationStack.undo();
        undo.enabled: UM.OperationStack.canUndo;
        redo.onTriggered: UM.OperationStack.redo();
        redo.enabled: UM.OperationStack.canRedo;

        deleteSelection.onTriggered:
        {
            if(objectContextMenu.objectId != 0)
            {
                Printer.deleteObject(objectContextMenu.objectId);
            }
        }

        deleteObject.onTriggered:
        {
            if(objectContextMenu.objectId != 0)
            {
                Printer.deleteObject(objectContextMenu.objectId);
                objectContextMenu.objectId = 0;
            }
        }

        multiplyObject.onTriggered:
        {
            if(objectContextMenu.objectId != 0)
            {
                Printer.multiplyObject(objectContextMenu.objectId, 1);
                objectContextMenu.objectId = 0;
            }
        }

        centerObject.onTriggered:
        {
            if(objectContextMenu.objectId != 0)
            {
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

        preferences.onTriggered: { preferences.visible = true; }
        configureMachines.onTriggered: { preferences.visible = true; preferences.setPage(3); }
        manageProfiles.onTriggered: { preferences.visible = true; preferences.setPage(4); }

        documentation.onTriggered: CuraActions.openDocumentation();
        reportBug.onTriggered: CuraActions.openBugReportPage();
        showEngineLog.onTriggered: engineLog.visible = true;
        about.onTriggered: aboutDialog.visible = true;
        toggleFullScreen.onTriggered: base.toggleFullscreen()
    }

    Menu
    {
        id: objectContextMenu;

        property variant objectId: -1;
        MenuItem { action: actions.centerObject; }
        MenuItem { action: actions.deleteObject; }
        MenuItem { action: actions.multiplyObject; }
        MenuSeparator { }
        MenuItem { action: actions.deleteAll; }
        MenuItem { action: actions.reloadAll; }
        MenuItem { action: actions.resetAllTranslation; }
        MenuItem { action: actions.resetAll; }
        MenuItem { action: actions.groupObjects;}
        MenuItem { action: actions.mergeObjects;}
        MenuItem { action: actions.unGroupObjects;}
    }

    Menu
    {
        id: contextMenu;
        MenuItem { action: actions.deleteAll; }
        MenuItem { action: actions.reloadAll; }
        MenuItem { action: actions.resetAllTranslation; }
        MenuItem { action: actions.resetAll; }
        MenuItem { action: actions.groupObjects;}
        MenuItem { action: actions.mergeObjects;}
        MenuItem { action: actions.unGroupObjects;}
    }

    Connections
    {
        target: UM.Controller
        onContextMenuRequested:
        {
            if(objectId == 0)
            {
                contextMenu.popup();
            } else
            {
                objectContextMenu.objectId = objectId;
                objectContextMenu.popup();
            }
        }
    }

    FileDialog
    {
        id: openDialog;

        //: File open dialog title
        title: catalog.i18nc("@title:window","Open File")
        modality: UM.Application.platform == "linux" ? Qt.NonModal : Qt.WindowModal;
        //TODO: Support multiple file selection, workaround bug in KDE file dialog
        //selectMultiple: true

        signal hasMesh(string name)

        function sendMeshName(path){
            var fileName = path.slice(path.lastIndexOf("/") + 1)
            var fileBase = fileName.slice(0, fileName.lastIndexOf("."))
            openDialog.hasMesh(fileBase)
        }
        nameFilters: UM.MeshFileHandler.supportedReadFileTypes;

        onAccepted:
        {
            UM.MeshFileHandler.readLocalFile(fileUrl)
            openDialog.sendMeshName(fileUrl.toString())
        }
    }

    EngineLog
    {
        id: engineLog;
    }

    AddMachineWizard
    {
        id: addMachineWizard
    }


    AboutDialog
    {
        id: aboutDialog
    }

    Connections
    {
        target: Printer
        onRequestAddPrinter:
        {
            addMachineWizard.visible = true
            addMachineWizard.firstRun = false
        }
    }

    Component.onCompleted:
    {
        UM.Theme.load(UM.Resources.getPath(UM.Resources.Themes, "cura"))
        visible = true;
        addMachineTimer.start();
    }

    Timer
    {
        id: addMachineTimer;
        interval: 100;
        repeat: false;
        onTriggered:
        {
            if(UM.MachineManager.activeMachineInstance == "")
            {
                addMachineWizard.firstRun = true;
                addMachineWizard.open();
            }
        }
    }
}

