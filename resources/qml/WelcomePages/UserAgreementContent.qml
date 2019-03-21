// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.3 as UM
import Cura 1.1 as Cura

//
// This component contains the content for the "User Agreement" page of the welcome on-boarding process.
//
Item
{
    Column
    {
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: 20

        UM.I18nCatalog { id: catalog; name: "cura" }

        spacing: 40

        // Placeholder
        Label { text: " " }

        Label
        {
            id: titleLabel
            anchors.horizontalCenter: parent.horizontalCenter
            horizontalAlignment: Text.AlignHCenter
            text: catalog.i18nc("@label", "User Agreement")
            color: UM.Theme.getColor("primary_button")
            font: UM.Theme.getFont("large_bold")
            renderType: Text.NativeRendering
        }

        Label
        {
            width: parent.width * 2 / 3
            id: disclaimerLineLabel
            anchors.horizontalCenter: parent.horizontalCenter
            text: "<p><b>Disclaimer by Ultimaker</b></p>"
                + "<p>Please read this disclaimer carefully.</p>"
                + "<p>Except when otherwise stated in writing, Ultimaker provides any Ultimaker software or third party software \"As is\" without warranty of any kind. The entire risk as to the quality and perfoemance of Ultimaker software is with you.</p>"
                + "<p>Unless required by applicable law or agreed to in writing, in no event will Ultimaker be liable to you for damages, including any general, special, incidental, or consequential damages arising out of the use or inability to use any Ultimaker software or third party software.</p>"
            textFormat: Text.RichText
            wrapMode: Text.WordWrap
            font: UM.Theme.getFont("default")
            renderType: Text.NativeRendering
        }
    }

    Cura.PrimaryButton
    {
        id: agreeButton
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.margins: 40
        text: catalog.i18nc("@button", "Agree")
        width: UM.Theme.getSize("welcome_pages_button").width
        fixedWidthMode: true
        onClicked:
        {
            CuraApplication.writeToLog("i", "User accepted the User-Agreement.")
            CuraApplication.setNeedToShowUserAgreement(false)
            base.showNextPage()
        }
    }

    Cura.SecondaryButton
    {
        id: declineButton
        anchors.left: parent.left
        anchors.bottom: parent.bottom
        anchors.margins: 40
        text: catalog.i18nc("@button", "Decline and close")
        width: UM.Theme.getSize("welcome_pages_button").width
        fixedWidthMode: true
        onClicked:
        {
            CuraApplication.writeToLog("i", "User declined the User Agreement.")
            base.passLastPage()
            CuraApplication.closeApplication() // NOTE: Hard exit, don't use if anything needs to be saved!
        }
    }
}
