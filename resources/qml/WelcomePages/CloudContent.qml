// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.3 as UM
import Cura 1.1 as Cura


//
// This component contains the content for the "Ultimaker Cloud" page of the welcome on-boarding process.
//
Item
{
    UM.I18nCatalog { id: catalog; name: "cura" }

    Label
    {
        id: titleLabel
        anchors.top: parent.top
        anchors.topMargin: 40
        anchors.horizontalCenter: parent.horizontalCenter
        horizontalAlignment: Text.AlignHCenter
        text: catalog.i18nc("@label", "Ultimaker Cloud")
        color: UM.Theme.getColor("primary_button")
        font: UM.Theme.getFont("large_bold")
        renderType: Text.NativeRendering
    }

    Column
    {
        anchors.top: titleLabel.bottom
        anchors.topMargin: 80
        anchors.horizontalCenter: parent.horizontalCenter

        spacing: 60

        Image
        {
            id: cloudImage
            anchors.horizontalCenter: parent.horizontalCenter
            source: UM.Theme.getImage("first_run_ultimaker_cloud")
        }

        Column
        {
            anchors.horizontalCenter: parent.horizontalCenter

            spacing: 30

            Label
            {
                id: highlightTextLabel
                anchors.horizontalCenter: parent.horizontalCenter
                horizontalAlignment: Text.AlignHCenter
                text: catalog.i18nc("@text", "The next generation 3D printing workflow")
                textFormat: Text.RichText
                color: UM.Theme.getColor("text_light_blue")
                font: UM.Theme.getFont("medium")
                renderType: Text.NativeRendering
            }

            Label
            {
                id: textLabel
                anchors.horizontalCenter: parent.horizontalCenter
                text: {
                    var t = "<p>- Send print jobs to Ultimaker printers outside your local network<p>"
                    t += "<p>- Store your Ultimaker Cura settings in the cloud for use anywhere</p>"
                    t += "<p>- Get exclusive access to material profiles from leading brands</p>"
                    catalog.i18nc("@text", t)
                }
                textFormat: Text.RichText
                font: UM.Theme.getFont("medium")
                renderType: Text.NativeRendering
            }
        }
    }

    Cura.PrimaryButton
    {
        id: finishButton
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.margins: 40
        text: catalog.i18nc("@button", "Finish")
        width: UM.Theme.getSize("welcome_pages_button").width
        fixedWidthMode: true
        onClicked: base.showNextPage()
    }

    Cura.SecondaryButton
    {
        id: createAccountButton
        anchors.left: parent.left
        anchors.verticalCenter: finishButton.verticalCenter
        anchors.margins: 40
        text: catalog.i18nc("@button", "Create an account")
        width: UM.Theme.getSize("welcome_pages_button").width
        fixedWidthMode: true
        onClicked: Qt.openUrlExternally(CuraApplication.ultimakerCloudAccountRootUrl + "/app/create")
    }

    Cura.SecondaryButton
    {
        id: signInButton
        anchors.left: createAccountButton.right
        anchors.verticalCenter: finishButton.verticalCenter
        text: catalog.i18nc("@button", "Sign in")
        width: UM.Theme.getSize("welcome_pages_button").width
        shadowEnabled: false
        color: "transparent"
        hoverColor: "transparent"
        textHoverColor: UM.Theme.getColor("text_light_blue")
        fixedWidthMode: true
        onClicked: Cura.API.account.login()
    }
}
