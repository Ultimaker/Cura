// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import QtQuick.Layouts 1.1
import QtQuick.Dialogs 1.2

import UM 1.3 as UM
import Cura 1.1 as Cura

import "../Menus"
import "../Dialogs"

Item
{
    id: menu
    width: applicationMenu.width
    height: applicationMenu.height
    property alias window: applicationMenu.window

    UM.ApplicationMenu
    {
        id: applicationMenu

        Menu
        {
            id: fileMenu
            title: catalog.i18nc("@title:menu menubar:toplevel", "&File")

            MenuItem
            {
                id: newProjectMenu
                action: Cura.Actions.newProject
            }

            MenuItem
            {
                id: openMenu
                action: Cura.Actions.open
            }

            RecentFilesMenu { }

            MenuItem
            {
                id: saveWorkspaceMenu
                text: catalog.i18nc("@title:menu menubar:file", "&Save...")
                onTriggered:
                {
                    var args = { "filter_by_machine": false, "file_type": "workspace", "preferred_mimetypes": "application/vnd.ms-package.3dmanufacturing-3dmodel+xml" };
                    if(UM.Preferences.getValue("cura/dialog_on_project_save"))
                    {
                        saveWorkspaceDialog.args = args
                        saveWorkspaceDialog.open()
                    }
                    else
                    {
                        UM.OutputDeviceManager.requestWriteToDevice("local_file", PrintInformation.jobName, args)
                    }
                }
            }

            MenuSeparator { }

            MenuItem
            {
                id: saveAsMenu
                text: catalog.i18nc("@title:menu menubar:file", "&Export...")
                onTriggered:
                {
                    var localDeviceId = "local_file"
                    UM.OutputDeviceManager.requestWriteToDevice(localDeviceId, PrintInformation.jobName, { "filter_by_machine": false, "preferred_mimetypes": "application/vnd.ms-package.3dmanufacturing-3dmodel+xml"})
                }
            }

            MenuItem
            {
                id: exportSelectionMenu
                text: catalog.i18nc("@action:inmenu menubar:file", "Export Selection...")
                enabled: UM.Selection.hasSelection
                iconName: "document-save-as"
                onTriggered: UM.OutputDeviceManager.requestWriteSelectionToDevice("local_file", PrintInformation.jobName, { "filter_by_machine": false, "preferred_mimetypes": "application/vnd.ms-package.3dmanufacturing-3dmodel+xml"})
            }

            MenuSeparator { }

            MenuItem
            {
                id: reloadAllMenu
                action: Cura.Actions.reloadAll
            }

            MenuSeparator { }

            MenuItem { action: Cura.Actions.quit }
        }

        Menu
        {
            title: catalog.i18nc("@title:menu menubar:toplevel", "&Edit")

            MenuItem { action: Cura.Actions.undo }
            MenuItem { action: Cura.Actions.redo }
            MenuSeparator { }
            MenuItem { action: Cura.Actions.selectAll }
            MenuItem { action: Cura.Actions.arrangeAll }
            MenuItem { action: Cura.Actions.deleteSelection }
            MenuItem { action: Cura.Actions.deleteAll }
            MenuItem { action: Cura.Actions.resetAllTranslation }
            MenuItem { action: Cura.Actions.resetAll }
            MenuSeparator { }
            MenuItem { action: Cura.Actions.groupObjects }
            MenuItem { action: Cura.Actions.mergeObjects }
            MenuItem { action: Cura.Actions.unGroupObjects }
        }

        ViewMenu { title: catalog.i18nc("@title:menu", "&View") }

        Menu
        {
            id: settingsMenu
            title: catalog.i18nc("@title:menu", "&Settings")

            PrinterMenu { title: catalog.i18nc("@title:menu menubar:settings", "&Printer") }

            Instantiator
            {
                model: Cura.ExtrudersModel { simpleNames: true }
                Menu
                {
                    title: model.name

                    NozzleMenu { title: Cura.MachineManager.activeDefinitionVariantsName; visible: Cura.MachineManager.hasVariants; extruderIndex: index }
                    MaterialMenu { title: catalog.i18nc("@title:menu", "&Material"); visible: Cura.MachineManager.hasMaterials; extruderIndex: index }

                    MenuSeparator
                    {
                        visible: Cura.MachineManager.hasVariants || Cura.MachineManager.hasMaterials
                    }

                    MenuItem
                    {
                        text: catalog.i18nc("@action:inmenu", "Set as Active Extruder")
                        onTriggered: Cura.MachineManager.setExtruderIndex(model.index)
                    }

                    MenuItem
                    {
                        text: catalog.i18nc("@action:inmenu", "Enable Extruder")
                        onTriggered: Cura.MachineManager.setExtruderEnabled(model.index, true)
                        visible: !Cura.MachineManager.getExtruder(model.index).isEnabled
                    }

                    MenuItem
                    {
                        text: catalog.i18nc("@action:inmenu", "Disable Extruder")
                        onTriggered: Cura.MachineManager.setExtruderEnabled(model.index, false)
                        visible: Cura.MachineManager.getExtruder(model.index).isEnabled
                        enabled: Cura.MachineManager.numberExtrudersEnabled > 1
                    }

                }
                onObjectAdded: settingsMenu.insertItem(index, object)
                onObjectRemoved: settingsMenu.removeItem(object)
            }

            // TODO Only show in dev mode. Remove check when feature ready
            BuildplateMenu
            {
                title: catalog.i18nc("@title:menu", "&Build plate")
                visible: CuraSDKVersion == "dev" && Cura.MachineManager.hasVariantBuildplates
            }
            ProfileMenu { title: catalog.i18nc("@title:settings", "&Profile") }

            MenuSeparator { }

            MenuItem { action: Cura.Actions.configureSettingVisibility }
        }

        Menu
        {
            id: extensionMenu
            title: catalog.i18nc("@title:menu menubar:toplevel", "E&xtensions")

            Instantiator
            {
                id: extensions
                model: UM.ExtensionModel { }

                Menu
                {
                    id: sub_menu
                    title: model.name;
                    visible: actions != null
                    enabled: actions != null
                    Instantiator
                    {
                        model: actions
                        MenuItem
                        {
                            text: model.text
                            onTriggered: extensions.model.subMenuTriggered(name, model.text)
                        }
                        onObjectAdded: sub_menu.insertItem(index, object)
                        onObjectRemoved: sub_menu.removeItem(object)
                    }
                }

                onObjectAdded: extensionMenu.insertItem(index, object)
                onObjectRemoved: extensionMenu.removeItem(object)
            }
        }

        Menu
        {
            id: plugin_menu
            title: catalog.i18nc("@title:menu menubar:toplevel", "&Toolbox")

            MenuItem { action: Cura.Actions.browsePackages }
        }

        Menu
        {
            id: preferencesMenu
            title: catalog.i18nc("@title:menu menubar:toplevel", "P&references")

            MenuItem { action: Cura.Actions.preferences }
        }

        Menu
        {
            id: helpMenu
            title: catalog.i18nc("@title:menu menubar:toplevel", "&Help")

            MenuItem { action: Cura.Actions.showProfileFolder }
            MenuItem { action: Cura.Actions.documentation }
            MenuItem { action: Cura.Actions.reportBug }
            MenuSeparator { }
            MenuItem { action: Cura.Actions.about }
        }
    }

    // ###############################################################################################
    // Definition of other components that are linked to the menus
    // ###############################################################################################

    WorkspaceSummaryDialog
    {
        id: saveWorkspaceDialog
        property var args
        onYes: UM.OutputDeviceManager.requestWriteToDevice("local_file", PrintInformation.jobName, args)
    }

    MessageDialog
    {
        id: newProjectDialog
        modality: Qt.ApplicationModal
        title: catalog.i18nc("@title:window", "New project")
        text: catalog.i18nc("@info:question", "Are you sure you want to start a new project? This will clear the build plate and any unsaved settings.")
        standardButtons: StandardButton.Yes | StandardButton.No
        icon: StandardIcon.Question
        onYes:
        {
            CuraApplication.deleteAll();
            Cura.Actions.resetProfile.trigger();
        }
    }

    UM.ExtensionModel
    {
        id: curaExtensions
    }

    // ###############################################################################################
    // Definition of all the connections
    // ###############################################################################################

    Connections
    {
        target: Cura.Actions.newProject
        onTriggered:
        {
            if(Printer.platformActivity || Cura.MachineManager.hasUserSettings)
            {
                newProjectDialog.visible = true
            }
        }
    }

    // show the plugin browser dialog
    Connections
    {
        target: Cura.Actions.browsePackages
        onTriggered:
        {
            curaExtensions.callExtensionMethod("Toolbox", "browsePackages")
        }
    }
}