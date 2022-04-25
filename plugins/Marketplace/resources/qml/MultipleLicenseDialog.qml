// Copyright (c) 2021 Ultimaker B.V.
// Marketplace is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Window 2.2
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3

import UM 1.5 as UM
import Cura 1.6 as Cura

UM.Dialog
{
    id: licenseDialog
    title: licenseModel.dialogTitle

    minimumWidth: UM.Theme.getSize("modal_window_minimum").width
    minimumHeight: UM.Theme.getSize("modal_window_minimum").height
    width: minimumWidth
    height: minimumHeight
    backgroundColor: UM.Theme.getColor("main_background")
    margin: UM.Theme.getSize("default_margin").width

    ColumnLayout
    {
        anchors.fill: parent
        spacing: UM.Theme.getSize("thick_margin").height

        UM.I18nCatalog { id: catalog; name: "cura" }

        UM.Label
        {
            id: licenseHeader
            Layout.fillWidth: true
            text: catalog.i18nc("@label", "You need to accept the license to install the package")
        }

        Row {
            id: packageRow

            Layout.fillWidth: true
            height: childrenRect.height
            spacing: UM.Theme.getSize("default_margin").width
            leftPadding: UM.Theme.getSize("narrow_margin").width

            Image
            {
                id: icon
                width: UM.Theme.getSize("card_icon").width
                height: width
                sourceSize.width: width
                sourceSize.height: height
                fillMode: Image.PreserveAspectFit
                source: licenseModel.iconUrl || Qt.resolvedUrl("../images/placeholder.svg")
                mipmap: true
            }

            UM.Label
            {
                id: packageName
                text: licenseModel.packageName

                font.bold: true
                anchors.verticalCenter: icon.verticalCenter
                height: contentHeight
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
            text: licenseModel.acceptButtonText
            onClicked:  handler.onLicenseAccepted()
        }
    ]

    leftButtons:
    [
        Cura.SecondaryButton
        {
            id: declineButton
            text: licenseModel.declineButtonText
            onClicked: handler.onLicenseDeclined()
        }
    ]
}
