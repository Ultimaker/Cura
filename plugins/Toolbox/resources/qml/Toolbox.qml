// Copyright (c) 2018 Ultimaker B.V.
// Toolbox is released under the terms of the LGPLv3 or higher.

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
    title: catalog.i18nc("@title:tab", "Toolbox")
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
                visible: toolbox.viewCategory != "installed" && toolbox.viewPage == "loading"
            }
            ToolboxDownloadsPage
            {
                id: viewDownloads
                visible: toolbox.viewCategory != "installed" && toolbox.viewPage == "overview"
            }
            ToolboxDetailPage
            {
                id: viewDetail
                visible: toolbox.viewCategory != "installed" && toolbox.viewPage == "detail"
            }
            ToolboxAuthorPage
            {
                id: viewAuthor
                visible: toolbox.viewCategory != "installed" && toolbox.viewPage == "author"
            }
            ToolboxInstalledPage
            {
                id: installedPluginList
                visible: toolbox.viewCategory == "installed"
            }
        }
        ToolboxShadow
        {
            anchors.top: header.bottom
        }
        ToolboxFooter
        {
            id: footer
            visible: toolbox.restartRequired
            height: toolbox.restartRequired ? UM.Theme.getSize("base_unit").height * 5 : 0
        }
        ToolboxShadow
        {
            visible: toolbox.restartRequired
            anchors.bottom: footer.top
            reversed: true
        }

        UM.I18nCatalog { id: catalog; name: "cura" }

        Connections
        {
            target: toolbox
            onShowLicenseDialog:
            {
                licenseDialog.pluginName = toolbox.getLicenseDialogPluginName();
                licenseDialog.licenseContent = toolbox.getLicenseDialogLicenseContent();
                licenseDialog.pluginFileLocation = toolbox.getLicenseDialogPluginFileLocation();
                licenseDialog.show();
            }
        }
        Connections
        {
            target: toolbox
            onShowRestartDialog:
            {
                restartDialog.message = toolbox.getRestartDialogMessage();
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
