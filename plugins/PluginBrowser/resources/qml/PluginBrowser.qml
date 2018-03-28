// Copyright (c) 2018 Ultimaker B.V.
// PluginBrowser is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Dialogs 1.1
import QtQuick.Window 2.2
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4

// TODO: Switch to QtQuick.Controls 2.x and remove QtQuick.Controls.Styles

import UM 1.1 as UM

Window
    {
    id: base
    title: catalog.i18nc("@title:tab", "Plugins");
    width: 800 * screenScaleFactor
    height: 640 * screenScaleFactor
    minimumWidth: 800 * screenScaleFactor
    maximumWidth: 800 * screenScaleFactor
    minimumHeight: 350 * screenScaleFactor
    color: UM.Theme.getColor("sidebar")
    Item
    {
        id: view
        anchors.fill: parent
        ToolboxHeader
        {
            id: topBar
        }
        Rectangle
        {
            id: mainView
            width: parent.width
            anchors
            {
                top: topBar.bottom
                bottom: bottomBar.top
            }
            ToolboxViewDownloads
            {
                id: viewDownloads
                visible: manager.viewing == "available" ? true : false
            }
            ToolboxViewInstalled
            {
                id: installedPluginList
                visible: manager.viewing == "installed" ? true : false
            }
        }
        Rectangle
        {
            anchors
            {
                top: topBar.bottom
            }
            width: parent.width
            height: 8
            gradient: Gradient
            {
                GradientStop
                {
                    position: 0.0
                    color: Qt.rgba(0,0,0,0.1)
                }
                GradientStop
                {
                    position: 1.0
                    color: Qt.rgba(0,0,0,0)
                }
            }
        }
        ToolboxFooter
        {
            id: bottomBar
        }
        Rectangle
        {
            anchors
            {
                top: bottomBar.top
            }
            width: parent.width
            height: 8
            gradient: Gradient
            {
                GradientStop
                {
                    position: 0.0
                    color: Qt.rgba(0,0,0,0.1)
                }
                GradientStop
                {
                    position: 1.0
                    color: Qt.rgba(0,0,0,0)
                }
            }
        }




        UM.I18nCatalog { id: catalog; name: "cura" }

        Connections
        {
            target: manager
            onShowLicenseDialog:
            {
                licenseDialog.pluginName = manager.getLicenseDialogPluginName();
                licenseDialog.licenseContent = manager.getLicenseDialogLicenseContent();
                licenseDialog.pluginFileLocation = manager.getLicenseDialogPluginFileLocation();
                licenseDialog.show();
            }
        }
        Connections
        {
            target: manager
            onShowRestartDialog:
            {
                restartDialog.message = manager.getRestartDialogMessage();
                restartDialog.show();
            }
        }
        ToolboxLicenseDialog
        {
            id: licenseDialog
        }

        ToolboxRestartDialog
        {
            id: restartDialog
        }
    }
}
