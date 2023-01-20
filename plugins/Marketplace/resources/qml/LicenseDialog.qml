//Copyright (c) 2021 Ultimaker B.V.
//Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Window 2.2
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3

import UM 1.6 as UM
import Cura 1.6 as Cura

UM.Dialog
{
    id: licenseDialog
    title: catalog.i18nc("@button", "Plugin license agreement")
    minimumWidth: UM.Theme.getSize("modal_window_minimum").width
    minimumHeight: UM.Theme.getSize("modal_window_minimum").height
    width: minimumWidth
    height: minimumHeight
    backgroundColor: UM.Theme.getColor("main_background")

    property variant catalog: UM.I18nCatalog { name: "cura" }

    ColumnLayout
    {
        anchors.fill: parent
        spacing: UM.Theme.getSize("thick_margin").height

        Row
        {
            Layout.fillWidth: true
            height: childrenRect.height
            spacing: UM.Theme.getSize("default_margin").width
            leftPadding: UM.Theme.getSize("narrow_margin").width

            UM.ColorImage
            {
                id: icon
                width: UM.Theme.getSize("marketplace_large_icon").width
                height: UM.Theme.getSize("marketplace_large_icon").height
                color: UM.Theme.getColor("text")
                source: UM.Theme.getIcon("Certificate", "high")
            }

            UM.Label
            {
                text: catalog.i18nc("@text", "Please read and agree with the plugin licence.")
                font: UM.Theme.getFont("large")
                anchors.verticalCenter: icon.verticalCenter
                height: UM.Theme.getSize("marketplace_large_icon").height
                verticalAlignment: Qt.AlignVCenter
            }
        }

        Cura.ScrollableTextArea
        {
            Layout.fillWidth: true
            Layout.fillHeight: true
            anchors.topMargin: UM.Theme.getSize("default_margin").height

            textArea.text: licenseContent
            textArea.readOnly: true
        }

    }
    rightButtons:
    [
        Cura.PrimaryButton
        {
            text: catalog.i18nc("@button", "Accept")
            onClicked: handler.onLicenseAccepted(packageId)
        }
    ]

    leftButtons:
    [
        Cura.SecondaryButton
        {
            text: catalog.i18nc("@button", "Decline")
            onClicked: handler.onLicenseDeclined(packageId)
        }
    ]

    onAccepted: handler.onLicenseAccepted(packageId)
    onRejected: handler.onLicenseDeclined(packageId)
    onClosing: handler.onLicenseDeclined(packageId)
}
