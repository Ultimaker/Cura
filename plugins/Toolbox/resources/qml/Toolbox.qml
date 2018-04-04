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
    property bool dataReady: manager.dataReady
    title: catalog.i18nc("@title:tab", "Toolbox");
    modality: Qt.ApplicationModal
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
            color: "transparent"
            anchors
            {
                top: topBar.bottom
                bottom: bottomBar.top
            }
            ToolboxLoading
            {
                id: loading
                visible: !dataReady && manager.currentView != "installed"
            }
            ToolboxDownloadsPage
            {
                id: viewDownloads
                visible: dataReady && manager.currentView != "installed" && manager.detailView == ""
            }
            ToolboxDetailsPage
            {
                id: viewDetail
                visible: dataReady && manager.currentView != "installed" && manager.detailView != ""
            }
            ToolboxInstalledPage
            {
                id: installedPluginList
                visible: dataReady && manager.currentView == "installed"
            }
        }
        ToolboxShadow
        {
            anchors
            {
                top: topBar.bottom
            }
        }
        ToolboxFooter
        {
            id: bottomBar
        }
        ToolboxShadow
        {
            anchors
            {
                top: bottomBar.top
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
