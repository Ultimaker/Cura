// Copyright (c) 2021 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.4
import QtQuick.Dialogs 1.2

import UM 1.5 as UM
import Cura 1.1 as Cura

import "../Menus"
import "../Dialogs"

Item
{
    id: menu
    width: parent.width
    height: applicationMenu.height

    Component
    {
        id: menuBarComponent
        MenuBarItem
        {
            id: menuBarItem

            function replaceText(txt)
            {
                var index = txt.indexOf("&")
                if(index >= 0)
                {
                    txt = txt.replace(txt.substr(index, 2), ("<u>" + txt.substr(index + 1, 1) +"</u>"))
                }
                return txt
            }

            contentItem: Label {
                text: replaceText(menuBarItem.text)
                color: "white"
                verticalAlignment: Text.AlignVCenter
                textFormat: Text.RichText
            }
        }
    }

    MenuBar
    {
        id: applicationMenu
        width: parent.width
        delegate: menuBarComponent
        FileMenu {}

        EditMenu {}
        ViewMenu {}

        background: Rectangle {}

        SettingsMenu
        {
            //On MacOS, don't translate the "Settings" word.
            //Qt moves the "settings" entry to a different place, and if it got renamed can't find it again when it
            //attempts to delete the item upon closing the application, causing a crash.
            //In the new location, these items are translated automatically according to the system's language.
            //For more information, see:
            //- https://doc.qt.io/qt-5/macos-issues.html#menu-bar
            //- https://doc.qt.io/qt-5/qmenubar.html#qmenubar-as-a-global-menu-bar
            title: (Qt.platform.os == "osx") ? "&Settings" : catalog.i18nc("@title:menu menubar:toplevel", "&Settings")
        }

        ExtensionMenu {}

        PreferencesMenu {}

        HelpMenu {}

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
            CuraApplication.resetWorkspace()
            Cura.Actions.resetProfile.trigger()
            UM.Controller.setActiveStage("PrepareStage")
        }
    }

    // ###############################################################################################
    // Definition of all the connections
    // ###############################################################################################

    Connections
    {
        target: Cura.Actions.newProject
        function onTriggered()
        {
            if(Printer.platformActivity || Cura.MachineManager.hasUserSettings)
            {
                newProjectDialog.visible = true
            }
        }
    }

    // show the Toolbox
    Connections
    {
        target: Cura.Actions.browsePackages
        function onTriggered()
        {
            curaExtensions.callExtensionMethod("Toolbox", "launch")
        }
    }

    // Show the Marketplace dialog at the materials tab
    Connections
    {
        target: Cura.Actions.marketplaceMaterials
        function onTriggered()
        {
            curaExtensions.callExtensionMethod("Toolbox", "launch")
            curaExtensions.callExtensionMethod("Toolbox", "setViewCategoryToMaterials")
        }
    }
}