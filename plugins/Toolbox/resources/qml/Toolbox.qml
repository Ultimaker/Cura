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
    width: 720 * screenScaleFactor
    height: 640 * screenScaleFactor
    minimumWidth: 720 * screenScaleFactor
    maximumWidth: 720 * screenScaleFactor
    minimumHeight: 350 * screenScaleFactor
    color: UM.Theme.getColor("sidebar")
    Item
    {
        anchors.fill: parent
        ToolboxHeader
        {
            id: header
        }
        Rectangle
        {
            id: mainView
            width: parent.width
            color: "transparent"
            anchors
            {
                top: header.bottom
                bottom: footer.top
            }
            // TODO: This could be improved using viewFilter instead of viewCategory
            ToolboxLoadingPage
            {
                id: viewLoading
                visible: manager.viewCategory != "installed" && manager.viewPage == "loading"
            }
            ToolboxDownloadsPage
            {
                id: viewDownloads
                visible: manager.viewCategory != "installed" && manager.viewPage == "overview"
            }
            ToolboxDetailPage
            {
                id: viewDetail
                visible: manager.viewCategory != "installed" && manager.viewPage == "detail"
            }
            ToolboxAuthorPage
            {
                id: viewAuthor
                visible: manager.viewCategory != "installed" && manager.viewPage == "author"
            }
            ToolboxInstalledPage
            {
                id: installedPluginList
                visible: manager.viewCategory == "installed"
            }
        }
        ToolboxShadow
        {
            anchors.top: header.bottom
        }
        ToolboxFooter
        {
            id: footer
        }
        ToolboxShadow
        {
            anchors.top: footer.top
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
