// Copyright (c) 2018 Ultimaker B.V.
// Toolbox is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Dialogs 1.1
import QtQuick.Window 2.2
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4

// TODO: Switch to QtQuick.Controls 2.x and remove QtQuick.Controls.Styles

import UM 1.1 as UM
import Cura 1.6 as Cura

UM.Dialog
{
    id: licenseDialog
    title: licenseModel.dialogTitle
    minimumWidth: UM.Theme.getSize("license_window_minimum").width
    minimumHeight: UM.Theme.getSize("license_window_minimum").height
    width: minimumWidth
    height: minimumHeight
    backgroundColor: UM.Theme.getColor("main_background")
    margin: screenScaleFactor * 10

    Item
    {
        anchors.fill: parent

        UM.I18nCatalog{id: catalog; name: "cura"}

        Label
        {
            id: licenseHeader
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            text: licenseModel.headerText
            wrapMode: Text.Wrap
            renderType: Text.NativeRendering
        }
        TextArea
        {
            id: licenseText
            anchors.top: licenseHeader.bottom
            anchors.bottom: parent.bottom
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.topMargin: UM.Theme.getSize("default_margin").height
            readOnly: true
            text: licenseModel.licenseText
        }
    }
    rightButtons:
    [
        Cura.PrimaryButton
        {
            leftPadding: UM.Theme.getSize("dialog_primary_button_padding").width
            rightPadding: UM.Theme.getSize("dialog_primary_button_padding").width

            text: catalog.i18nc("@button", "Agree")
            onClicked: { handler.onLicenseAccepted() }
        }
    ]

    leftButtons:
    [
        Cura.SecondaryButton
        {
            id: declineButton
            text: catalog.i18nc("@button", "Decline and remove from account")
            onClicked: { handler.onLicenseDeclined() }
        }
    ]
}
