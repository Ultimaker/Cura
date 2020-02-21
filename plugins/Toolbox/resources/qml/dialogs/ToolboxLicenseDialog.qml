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
    title: licenseModel.dialogTitle
    minimumWidth: UM.Theme.getSize("license_window_minimum").width
    minimumHeight: UM.Theme.getSize("license_window_minimum").height
    width: minimumWidth
    height: minimumHeight
    backgroundColor: UM.Theme.getColor("main_background")
    margin: screenScaleFactor * 10

    ColumnLayout
    {
        anchors.fill: parent
        spacing: UM.Theme.getSize("thick_margin").height

        UM.I18nCatalog{id: catalog; name: "cura"}

        Label
        {
            id: licenseHeader
            Layout.fillWidth: true
            text: catalog.i18nc("@label", "You need to accept the license to install the package")
            color: UM.Theme.getColor("text")
            wrapMode: Text.Wrap
            renderType: Text.NativeRendering
        }

        Row {
            id: packageRow

            anchors.left: parent.left
            anchors.right: parent.right
            height: childrenRect.height
            spacing: UM.Theme.getSize("default_margin").width
            leftPadding: UM.Theme.getSize("narrow_margin").width

            Image
            {
                id: icon
                width: 30 * screenScaleFactor
                height: width
                fillMode: Image.PreserveAspectFit
                source: licenseModel.iconUrl || "../../images/placeholder.svg"
                mipmap: true
            }

            Label
            {
                id: packageName
                text: licenseModel.packageName
                color: UM.Theme.getColor("text")
                font.bold: true
                anchors.verticalCenter: icon.verticalCenter
                height: contentHeight
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
            leftPadding: UM.Theme.getSize("dialog_primary_button_padding").width
            rightPadding: UM.Theme.getSize("dialog_primary_button_padding").width

            text: licenseModel.acceptButtonText
            onClicked: { handler.onLicenseAccepted() }
        }
    ]

    leftButtons:
    [
        Cura.SecondaryButton
        {
            id: declineButton
            text: licenseModel.declineButtonText
            onClicked: { handler.onLicenseDeclined() }
        }
    ]
}
