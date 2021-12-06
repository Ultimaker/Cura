// Copyright (c) 2018 Ultimaker B.V.
// Toolbox is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Dialogs 1.1
import QtQuick.Window 2.2
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3
import QtQuick.Controls.Styles 1.4

import UM 1.1 as UM
import Cura 1.6 as Cura

UM.Dialog
{
    id: licenseDialog
    title: catalog.i18nc("@button", "Plugin license agreement")
    minimumWidth: UM.Theme.getSize("license_window_minimum").width
    minimumHeight: UM.Theme.getSize("license_window_minimum").height
    width: minimumWidth
    height: minimumHeight
    backgroundColor: UM.Theme.getColor("main_background")

    ColumnLayout
    {
        anchors.fill: parent
        spacing: UM.Theme.getSize("thick_margin").height

        UM.I18nCatalog{id: catalog; name: "cura"}

        Row {
            Layout.fillWidth: true
            height: childrenRect.height
            spacing: UM.Theme.getSize("default_margin").width
            leftPadding: UM.Theme.getSize("narrow_margin").width

            UM.RecolorImage
            {
                width: UM.Theme.getSize("marketplace_large_icon").width
                height: UM.Theme.getSize("marketplace_large_icon").height
                color: UM.Theme.getColor("text")
                source: UM.Theme.getIcon("Certificate", "high")
            }

            Label
            {
                text: catalog.i18nc("@text", "Please read and agree with the plugin licence.")
                color: UM.Theme.getColor("text")
                font: UM.Theme.getFont("large")
                anchors.verticalCenter: icon.verticalCenter
                height: UM.Theme.getSize("marketplace_large_icon").height
                verticalAlignment: Qt.AlignVCenter
                wrapMode: Text.Wrap
                renderType: Text.NativeRendering
            }

        }

        Cura.ScrollableTextArea
        {

            Layout.fillWidth: true
            Layout.fillHeight: true
            anchors.topMargin: UM.Theme.getSize("default_margin").height

            textArea.text: licenseModel.licenseText
            textArea.readOnly: true
        }

    }
    rightButtons:
    [
        Cura.PrimaryButton
        {
            text: catalog.i18nc("@button", "Accept")
            onClicked: { handler.onLicenseAccepted() }
        }
    ]

    leftButtons:
    [
        Cura.SecondaryButton
        {
            text: catalog.i18nc("@button", "Decline")
            onClicked: { handler.onLicenseDeclined() }
        }
    ]
}
