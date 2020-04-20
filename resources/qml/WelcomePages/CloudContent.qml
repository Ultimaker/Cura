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

    property bool isLoggedIn: Cura.API.account.isLoggedIn

    onIsLoggedInChanged:
    {
        if(isLoggedIn)
        {
            // If the user created an account or logged in by pressing any button on this page, all the actions that
            // need / can be done by this page are completed, so we can just go to the next (if any).
            base.showNextPage()
        }
    }

    Label
    {
        id: titleLabel
        anchors.top: parent.top
        anchors.horizontalCenter: parent.horizontalCenter
        horizontalAlignment: Text.AlignHCenter
        text: catalog.i18nc("@label", "Sign in to Ultimaker Cloud")
        color: UM.Theme.getColor("primary_button")
        font: UM.Theme.getFont("huge")
        renderType: Text.NativeRendering
    }

    // Area where the cloud contents can be put. Pictures, texts and such.
    Item
    {
        id: cloudContentsArea
        anchors
        {
            top: titleLabel.bottom
            bottom: nextButton.top
            left: parent.left
            right: parent.right
            topMargin: UM.Theme.getSize("default_margin").height
        }

        // Pictures and texts are arranged using Columns with spacing. The whole picture and text area is centered in
        // the cloud contents area.
        Column
        {
            anchors.centerIn: parent
            width: parent.width
            height: childrenRect.height

            spacing: 20 * screenScaleFactor

            Image  // Cloud image
            {
                id: cloudImage
                anchors.horizontalCenter: parent.horizontalCenter
                source: UM.Theme.getImage("first_run_ultimaker_cloud")
            }

            Label  // A title-ish text
            {
                id: highlightTextLabel
                anchors.horizontalCenter: parent.horizontalCenter
                horizontalAlignment: Text.AlignHCenter
                text: catalog.i18nc("@text", "The next generation 3D printing workflow")
                textFormat: Text.RichText
                color: UM.Theme.getColor("primary")
                font: UM.Theme.getFont("medium")
                renderType: Text.NativeRendering
            }

            Label  // A number of text items
            {
                id: textLabel
                anchors.horizontalCenter: parent.horizontalCenter
                text:
                {
                    // There are 3 text items, each of which is translated separately as a single piece of text.
                    var full_text = ""
                    var t = ""

                    t = catalog.i18nc("@text", "- Send print jobs to Ultimaker printers outside of your local network")
                    full_text += "<p>" + t + "</p>"

                    t = catalog.i18nc("@text", "- Store your Ultimaker Cura settings in the cloud to use anywhere")
                    full_text += "<p>" + t + "</p>"

                    t = catalog.i18nc("@text", "- Get exclusive access to material profiles from leading brands")
                    full_text += "<p>" + t + "</p>"

                    return full_text
                }
                textFormat: Text.RichText
                font: UM.Theme.getFont("medium")
                color: UM.Theme.getColor("text")
                renderType: Text.NativeRendering
            }

            // "Sign in" and "Create an account" exist inside the column
            Cura.PrimaryButton
            {
                id: signInButton
                height: createAccountButton.height
                width: createAccountButton.width
                anchors.horizontalCenter: parent.horizontalCenter
                text: catalog.i18nc("@button", "Sign in")
                onClicked: Cura.API.account.login()
                // Content Item is used in order to align the text inside the button. Without it, when resizing the
                // button, the text will be aligned on the left
                contentItem: Text {
                    text: signInButton.text
                    font: UM.Theme.getFont("medium")
                    color: UM.Theme.getColor("primary_text")
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
            }

            Cura.SecondaryButton
            {
                id: createAccountButton
                anchors.horizontalCenter: parent.horizontalCenter
                text: catalog.i18nc("@button","Create an account")
                onClicked: Qt.openUrlExternally(CuraApplication.ultimakerCloudAccountRootUrl + "/app/create")
            }
        }


    }

    // The "Next" button exists on the bottom right
    Label
    {
        id: nextButton
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.leftMargin: UM.Theme.getSize("default_margin").width
        text: catalog.i18nc("@button", "Skip")
        color: UM.Theme.getColor("secondary_button_text")
        font: UM.Theme.getFont("medium")
        renderType: Text.NativeRendering

        MouseArea
        {
            anchors.fill: parent
            hoverEnabled: true
            onClicked: base.showNextPage()
            onEntered: parent.font.underline = true
            onExited: parent.font.underline = false
        }
    }
}
