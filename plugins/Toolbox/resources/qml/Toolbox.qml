// Copyright (c) 2018 Ultimaker B.V.
// Toolbox is released under the terms of the LGPLv3 or higher.

// Main window for the Toolbox

import QtQuick 2.2
import QtQuick.Dialogs 1.1
import QtQuick.Window 2.2
import UM 1.1 as UM

import "./pages"
import "./dialogs"
import "./components"

Window
{
    id: base
    property var selection: null
    title: catalog.i18nc("@title", "Marketplace")
    modality: Qt.ApplicationModal
    flags: Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint

    width: Math.floor(720 * screenScaleFactor)
    height: Math.floor(640 * screenScaleFactor)
    minimumWidth: width
    maximumWidth: minimumWidth
    minimumHeight: height
    maximumHeight: minimumHeight
    color: UM.Theme.getColor("main_background")
    UM.I18nCatalog
    {
        id: catalog
        name: "cura"
    }
    Item
    {
        anchors.fill: parent

        WelcomePage
        {
            visible: toolbox.viewPage === "welcome"
        }

        ToolboxHeader
        {
            id: header
            visible: toolbox.viewPage !== "welcome"
        }

        Item
        {
            id: mainView
            width: parent.width
            z: parent.z - 1
            anchors
            {
                top: header.bottom
                bottom: footer.top
            }
            // TODO: This could be improved using viewFilter instead of viewCategory
            ToolboxLoadingPage
            {
                id: viewLoading
                visible: toolbox.viewCategory !== "installed" && toolbox.viewPage === "loading"
            }
            ToolboxErrorPage
            {
                id: viewErrored
                visible: toolbox.viewCategory !== "installed" && toolbox.viewPage === "errored"
            }
            ToolboxDownloadsPage
            {
                id: viewDownloads
                visible: toolbox.viewCategory !== "installed" && toolbox.viewPage === "overview"
            }
            ToolboxDetailPage
            {
                id: viewDetail
                visible: toolbox.viewCategory !== "installed" && toolbox.viewPage === "detail"
            }
            ToolboxAuthorPage
            {
                id: viewAuthor
                visible: toolbox.viewCategory !== "installed" && toolbox.viewPage === "author"
            }
            ToolboxInstalledPage
            {
                id: installedPluginList
                visible: toolbox.viewCategory === "installed"
            }
        }

        ToolboxFooter
        {
            id: footer
            visible: toolbox.restartRequired
            height: visible ? UM.Theme.getSize("toolbox_footer").height : 0
        }
        // TODO: Clean this up:
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
        
        ToolboxLicenseDialog
        {
            id: licenseDialog
        }
    }
}
