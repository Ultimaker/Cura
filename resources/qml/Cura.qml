// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1
import QtQuick.Dialogs 1.1

import UM 1.2 as UM
import Cura 1.0 as Cura

import "."

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

        signal hasMesh(string name) //this signal sends the filebase name so it can be used for the JobSpecs.qml
        function getMeshName(path){
            //takes the path the complete path of the meshname and returns only the filebase
            var fileName = path.slice(path.lastIndexOf("/") + 1)
            var fileBase = fileName.slice(0, fileName.lastIndexOf("."))
            return fileBase
        }

        //DeleteSelection on the keypress backspace event
        Keys.onPressed: {
            if (event.key == Qt.Key_Backspace)
            {
                if(objectContextMenu.objectId != 0)
                {
                    Printer.deleteObject(objectContextMenu.objectId);
                }
            }
        }

        UM.ApplicationMenu
        {
            id: menu
            window: base

            Menu
            {
                id: fileMenu
                //: File menu
                title: catalog.i18nc("@title:menu menubar:toplevel","&File");

                MenuItem {
                    action: Actions.open;
                }

                Menu
                {
                    id: recentFilesMenu;
                    title: catalog.i18nc("@title:menu menubar:file", "Open &Recent")
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
                                var meshName = backgroundItem.getMeshName(modelData.toString())
                                backgroundItem.hasMesh(decodeURIComponent(meshName))
                            }
                        }
                        onObjectAdded: recentFilesMenu.insertItem(index, object)
                        onObjectRemoved: recentFilesMenu.removeItem(object)
                    }
                }

                MenuSeparator { }

                MenuItem
                {
                    text: catalog.i18nc("@action:inmenu menubar:file", "&Save Selection to File");
                    enabled: UM.Selection.hasSelection;
                    iconName: "document-save-as";
                    onTriggered: UM.OutputDeviceManager.requestWriteSelectionToDevice("local_file", Printer.jobName, { "filter_by_machine": false });
                }
                Menu
                {
                    id: saveAllMenu
                    title: catalog.i18nc("@title:menu menubar:file","Save &All")
                    iconName: "document-save-all";
                    enabled: devicesModel.rowCount() > 0 && UM.Backend.progress > 0.99;

                    Instantiator
                    {
                        model: UM.OutputDevicesModel { id: devicesModel; }

                        MenuItem
                        {
                            text: model.description;
                            onTriggered: UM.OutputDeviceManager.requestWriteToDevice(model.id, Printer.jobName, { "filter_by_machine": false });
                        }
                        onObjectAdded: saveAllMenu.insertItem(index, object)
                        onObjectRemoved: saveAllMenu.removeItem(object)
                    }
                }

                MenuItem { action: Actions.reloadAll; }

                MenuSeparator { }

                MenuItem { action: Actions.quit; }
            }

            Menu
            {
                //: Edit menu
                title: catalog.i18nc("@title:menu menubar:toplevel","&Edit");

                MenuItem { action: Actions.undo; }
                MenuItem { action: Actions.redo; }
                MenuSeparator { }
                MenuItem { action: Actions.deleteSelection; }
                MenuItem { action: Actions.deleteAll; }
                MenuItem { action: Actions.resetAllTranslation; }
                MenuItem { action: Actions.resetAll; }
                MenuSeparator { }
                MenuItem { action: Actions.groupObjects;}
                MenuItem { action: Actions.mergeObjects;}
                MenuItem { action: Actions.unGroupObjects;}
            }

            Menu
            {
                title: catalog.i18nc("@title:menu menubar:toplevel","&View");
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
            }
            Menu
            {
                id: machineMenu;
                //: Machine menu
                title: catalog.i18nc("@title:menu menubar:toplevel","&Printer");

                Instantiator
                {
                    model: UM.ContainerStacksModel
                    {
                        filter: {"type": "machine"}
                    }
                    MenuItem
                    {
                        text: model.name;
                        checkable: true;
                        checked: Cura.MachineManager.activeMachineId == model.id
                        exclusiveGroup: machineSelectionMenuGroup;
                        onTriggered: Cura.MachineManager.setActiveMachine(model.id);
                    }
                    onObjectAdded: machineMenu.insertItem(index, object)
                    onObjectRemoved: machineMenu.removeItem(object)
                }

                ExclusiveGroup { id: machineMenuGroup; }

                MenuSeparator { }

                Instantiator
                {
                    model: UM.InstanceContainersModel
                    {
                        filter:
                        {
                            "type": "variant",
                            "definition": Cura.MachineManager.activeDefinitionId //Only show variants of this machine
                        }
                    }
                    MenuItem {
                        text: model.name;
                        checkable: true;
                        checked: model.id == Cura.MachineManager.activeVariantId;
                        exclusiveGroup: machineVariantsGroup;
                        onTriggered: Cura.MachineManager.setActiveVariant(model.id)
                    }
                    onObjectAdded: machineMenu.insertItem(index, object)
                    onObjectRemoved: machineMenu.removeItem(object)
                }

                ExclusiveGroup { id: machineVariantsGroup; }

                MenuSeparator { visible: Cura.MachineManager.hasVariants; }

                MenuItem { action: Actions.addMachine; }
                MenuItem { action: Actions.configureMachines; }
            }

            Menu
            {
                id: profileMenu
                title: catalog.i18nc("@title:menu menubar:toplevel", "P&rofile")

                Instantiator
                {
                    id: profileMenuInstantiator
//                     model: UM.ProfilesModel {}
                    property int separatorIndex: -1

                    Loader {
                        property QtObject model_data: model
                        property int model_index: index
                        sourceComponent: profileMenuItemDelegate
                    }

                    onObjectAdded:
                    {
                        //Insert a separator between readonly and custom profiles
                        if(separatorIndex < 0 && index > 0) {
                            if(model.getItem(index-1).readOnly != model.getItem(index).readOnly) {
                                profileMenu.insertSeparator(index);
                                separatorIndex = index;
                            }
                        }
                        //Because of the separator, custom profiles move one index lower
                        profileMenu.insertItem((model.getItem(index).readOnly) ? index : index + 1, object.item);
                    }
                    onObjectRemoved:
                    {
                        //When adding a profile, the menu is rebuild by removing all items.
                        //If a separator was added, we need to remove that too.
                        if(separatorIndex >= 0)
                        {
                            profileMenu.removeItem(profileMenu.items[separatorIndex])
                            separatorIndex = -1;
                        }
                        profileMenu.removeItem(object.item);
                    }
                }

                ExclusiveGroup { id: profileMenuGroup; }

                Component
                {
                    id: profileMenuItemDelegate
                    MenuItem
                    {
                        id: item
                        text: model_data ? model_data.name : ""
                        checkable: true;
                        checked: model_data ? model_data.active : false;
                        exclusiveGroup: profileMenuGroup;
                        onTriggered:
                        {
                            UM.MachineManager.setActiveProfile(model_data.name);
                            if (!model_data.active) {
                                //Selecting a profile was canceled; undo menu selection
                                profileMenuInstantiator.model.setProperty(model_index, "active", false);
                                var activeProfileName = UM.MachineManager.activeProfile;
                                var activeProfileIndex = profileMenuInstantiator.model.find("name", activeProfileName);
                                profileMenuInstantiator.model.setProperty(activeProfileIndex, "active", true);
                            }
                        }
                    }
                }

                MenuSeparator { id: profileMenuSeparator }

                MenuItem { action: Actions.updateProfile; }
                MenuItem { action: Actions.resetProfile; }
                MenuItem { action: Actions.addProfile; }
                MenuSeparator { }
                MenuItem { action: Actions.manageProfiles; }
            }

            Menu
            {
                id: extension_menu
                //: Extensions menu
                title: catalog.i18nc("@title:menu menubar:toplevel","E&xtensions");

                Instantiator
                {
                    model: UM.ExtensionModel { }

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
                title: catalog.i18nc("@title:menu menubar:toplevel","&Settings");

                MenuItem { action: Actions.preferences; }
            }

            Menu
            {
                //: Help menu
                title: catalog.i18nc("@title:menu menubar:toplevel","&Help");

                MenuItem { action: Actions.showEngineLog; }
                MenuItem { action: Actions.documentation; }
                MenuItem { action: Actions.reportBug; }
                MenuSeparator { }
                MenuItem { action: Actions.about; }
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
                                var meshName = backgroundItem.getMeshName(drop.urls[i].toString())
                                backgroundItem.hasMesh(decodeURIComponent(meshName))
                            }
                        }
                    }
                }
            }

            JobSpecs
            {
                id: jobSpecs
                anchors
                {
                    bottom: parent.bottom;
                    right: sidebar.left;
                    bottomMargin: UM.Theme.getSize("default_margin").height;
                    rightMargin: UM.Theme.getSize("default_margin").width;
                }
            }

            UM.MessageStack
            {
                anchors
                {
                    horizontalCenter: parent.horizontalCenter
                    horizontalCenterOffset: -(UM.Theme.getSize("sidebar").width/ 2)
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
                anchors.topMargin: UM.Theme.getSize("default_margin").height;
                anchors.left: viewModeButton.left;
                //anchors.bottom: buttons.top;
                //anchors.bottomMargin: UM.Theme.getSize("default_margin").height;

                height: childrenRect.height;

                source: UM.ActiveView.valid ? UM.ActiveView.activeViewPanel : "";
            }

            Button
            {
                id: openFileButton;
                //style: UM.Backend.progress < 0 ? UM.Theme.styles.open_file_button : UM.Theme.styles.tool_button;
                text: catalog.i18nc("@action:button","Open File");
                iconSource: UM.Theme.getIcon("load")
                style: UM.Theme.styles.tool_button
                tooltip: '';
                anchors
                {
                    top: parent.top;
                    //topMargin: UM.Theme.getSize("loadfile_margin").height
                    left: parent.left;
                    //leftMargin: UM.Theme.getSize("loadfile_margin").width
                }
                action: Actions.open;
            }

            Image
            {
                id: logo
                anchors
                {
                    left: parent.left
                    leftMargin: UM.Theme.getSize("default_margin").width;
                    bottom: parent.bottom
                    bottomMargin: UM.Theme.getSize("default_margin").height;
                }

                source: UM.Theme.getImage("logo");
                width: UM.Theme.getSize("logo").width;
                height: UM.Theme.getSize("logo").height;
                z: -1;

                sourceSize.width: width;
                sourceSize.height: height;
            }

            Button
            {
                id: viewModeButton

                anchors
                {
                    top: toolbar.bottom;
                    topMargin: UM.Theme.getSize("window_margin").height;
                    left: parent.left;
                }
                text: catalog.i18nc("@action:button","View Mode");
                iconSource: UM.Theme.getIcon("viewmode");

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

                property int mouseX: base.mouseX
                property int mouseY: base.mouseY

                anchors {
                    top: openFileButton.bottom;
                    topMargin: UM.Theme.getSize("window_margin").height;
                    left: parent.left;
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

                width: UM.Theme.getSize("sidebar").width;

                addMachineAction: Actions.addMachine;
                configureMachinesAction: Actions.configureMachines;
                addProfileAction: Actions.addProfile;
                updateProfileAction: Actions.updateProfile;
                resetProfileAction: Actions.resetProfile;
                manageProfilesAction: Actions.manageProfiles;
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
            insertPage(0, catalog.i18nc("@title:tab","General"), Qt.resolvedUrl("GeneralPage.qml"));

            //: View preferences page title
            insertPage(1, catalog.i18nc("@title:tab","View"), Qt.resolvedUrl("ViewPage.qml"));

            insertPage(3, catalog.i18nc("@title:tab", "Printers"), Qt.resolvedUrl("MachinesPage.qml"));

            insertPage(4, catalog.i18nc("@title:tab", "Materials"), Qt.resolvedUrl("Preferences/MaterialsPage.qml"));

            insertPage(5, catalog.i18nc("@title:tab", "Profiles"), Qt.resolvedUrl("Preferences/ProfilesPage.qml"));

            //Force refresh
            setPage(0);
        }

        onVisibleChanged:
        {
            if(!visible)
            {
                // When the dialog closes, switch to the General page.
                // This prevents us from having a heavy page like Setting Visiblity active in the background.
                setPage(0);
            }
        }
    }

    Connections
    {
        target: Actions.preferences
        onTriggered: preferences.visible = true
    }

    Connections
    {
        target: Actions.addProfile
        onTriggered:
        {
            UM.MachineManager.createProfile();
            preferences.setPage(5);
            preferences.show();

            // Show the renameDialog after a very short delay so the preference page has time to initiate
            showProfileNameDialogTimer.start();
        }
    }

    Connections
    {
        target: Actions.configureMachines
        onTriggered:
        {
            preferences.visible = true;
            preferences.setPage(3);
        }
    }

    Connections
    {
        target: Actions.manageProfiles
        onTriggered:
        {
            preferences.visible = true;
            preferences.setPage(5);
        }
    }

    Connections
    {
        target: Actions.configureSettingVisibility
        onTriggered:
        {
            preferences.visible = true;
            preferences.setPage(2);
            preferences.getCurrentItem().scrollToSection(source.key);
        }
    }

    Timer
    {
        id: showProfileNameDialogTimer
        repeat: false
        interval: 1

        onTriggered: preferences.getCurrentItem().showProfileNameDialog()
    }

    Menu
    {
        id: objectContextMenu;

        property variant objectId: -1;
        MenuItem { action: Actions.centerObject; }
        MenuItem { action: Actions.deleteObject; }
        MenuItem { action: Actions.multiplyObject; }
        MenuSeparator { }
        MenuItem { action: Actions.deleteAll; }
        MenuItem { action: Actions.reloadAll; }
        MenuItem { action: Actions.resetAllTranslation; }
        MenuItem { action: Actions.resetAll; }
        MenuSeparator { }
        MenuItem { action: Actions.groupObjects; }
        MenuItem { action: Actions.mergeObjects; }
        MenuItem { action: Actions.unGroupObjects; }

        Connections
        {
            target: Actions.deleteObject
            onTriggered:
            {
                if(objectContextMenu.objectId != 0)
                {
                    Printer.deleteObject(objectContextMenu.objectId);
                    objectContextMenu.objectId = 0;
                }
            }
        }

        Connections
        {
            target: Actions.multiplyObject
            onTriggered:
            {
                if(objectContextMenu.objectId != 0)
                {
                    Printer.multiplyObject(objectContextMenu.objectId, 1);
                    objectContextMenu.objectId = 0;
                }
            }
        }

        Connections
        {
            target: Actions.centerObject
            onTriggered:
            {
                if(objectContextMenu.objectId != 0)
                {
                    Printer.centerObject(objectContextMenu.objectId);
                    objectContextMenu.objectId = 0;
                }
            }
        }
    }

    Menu
    {
        id: contextMenu;
        MenuItem { action: Actions.deleteAll; }
        MenuItem { action: Actions.reloadAll; }
        MenuItem { action: Actions.resetAllTranslation; }
        MenuItem { action: Actions.resetAll; }
        MenuSeparator { }
        MenuItem { action: Actions.groupObjects; }
        MenuItem { action: Actions.mergeObjects; }
        MenuItem { action: Actions.unGroupObjects; }
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

    Connections
    {
        target: Actions.quit
        onTriggered: base.visible = false;
    }

    Connections
    {
        target: Actions.toggleFullScreen
        onTriggered: base.toggleFullscreen();
    }

    FileDialog
    {
        id: openDialog;

        //: File open dialog title
        title: catalog.i18nc("@title:window","Open file")
        modality: UM.Application.platform == "linux" ? Qt.NonModal : Qt.WindowModal;
        //TODO: Support multiple file selection, workaround bug in KDE file dialog
        //selectMultiple: true
        nameFilters: UM.MeshFileHandler.supportedReadFileTypes;
        folder: Printer.getDefaultPath()
        onAccepted:
        {
            //Because several implementations of the file dialog only update the folder
            //when it is explicitly set.
            var f = folder;
            folder = f;

            UM.MeshFileHandler.readLocalFile(fileUrl)
            var meshName = backgroundItem.getMeshName(fileUrl.toString())
            backgroundItem.hasMesh(decodeURIComponent(meshName))
        }
    }

    Connections
    {
        target: Actions.open
        onTriggered: openDialog.open()
    }

    EngineLog
    {
        id: engineLog;
    }

    Connections
    {
        target: Actions.showEngineLog
        onTriggered: engineLog.visible = true;
    }

    AddMachineDialog
    {
        id: addMachineDialog
    }

    Connections
    {
        target: Actions.addMachine
        onTriggered: addMachineDialog.visible = true;
    }

    AboutDialog
    {
        id: aboutDialog
    }

    Connections
    {
        target: Actions.about
        onTriggered: aboutDialog.visible = true;
    }

    Connections
    {
        target: Printer
        onRequestAddPrinter:
        {
            addMachineDialog.visible = true
            addMachineDialog.firstRun = false
        }
    }

    Timer
    {
        id: startupTimer;
        interval: 100;
        repeat: false;
        running: true;
        onTriggered:
        {
            if(!base.visible)
            {
                base.visible = true;
                restart();
            }
            else if(Cura.MachineManager.activeMachineId == null || Cura.MachineManager.activeMachineId == "")
            {
                addMachineDialog.open();
            }
        }
    }
}

