// Copyright (c) 2018 Ultimaker B.V.
// Toolbox is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Dialogs 1.1
import QtQuick.Window 2.2
import UM 1.1 as UM

Window
{
    id: base
    property var selection: null
    title: catalog.i18nc("@title", "Marketplace")
    modality: Qt.ApplicationModal
    flags: Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint

    width: 720 * screenScaleFactor
    height: 640 * screenScaleFactor
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
        ToolboxHeader
        {
            id: header
        }

        Item
        {
            id: mainView
            width: parent.width
            z: -1
            anchors
            {
                top: header.bottom
                bottom: footer.top
            }

            Loader
            {
                anchors.fill:parent
                source:
                {
                    if(toolbox.viewCategory == "installed")
                    {
                        return "ToolboxInstalledPage.qml"
                    }

                    switch (toolbox.viewPage)
                    {
                        case "loading":
                            return "ToolboxLoadingPage.qml"
                        case "errored":
                            return "ToolboxErrorPage.qml"
                        case "overview":
                            return "ToolboxDownloadsPage.qml"
                        case "detail":
                            return "ToolboxDetailPage.qml"
                        case "author":
                            return "ToolboxAuthorPage.qml"
                    }
                }
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
