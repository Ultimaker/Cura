// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.4 as UM
import Cura 1.1 as Cura
import '../Account'


Item
{
    UM.I18nCatalog { id: catalog; name: "cura" }
    property int signInStatusCode: 200
    property bool emailErrorVisible: false
    property bool passwordErrorVisible: false

    Label
    {
        id: titleLabel
        anchors.top: parent.top
        anchors.horizontalCenter: parent.horizontalCenter
        horizontalAlignment: Text.AlignHCenter
        text: catalog.i18nc("@label", "BCN3D Cloud Account")
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
            bottom: skipButton.top
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

            Label  // A number of text items
            {
                id: textLabel
                anchors.horizontalCenter: parent.horizontalCenter
                text:
                {
                    // There are 3 text items, each of which is translated separately as a single piece of text.
                    var full_text = ""
                    var t = ""

                    t = catalog.i18nc("@text", "- Stay flexible by syncing your setup and loading it anywhere")
                    full_text += "<p>" + t + "</p>"

                    t = catalog.i18nc("@text", "- Increase efficiency with a remote workflow on BCN3D printers")
                    full_text += "<p>" + t + "</p>"

                    return full_text
                }
                textFormat: Text.RichText
                font: UM.Theme.getFont("medium")
                color: UM.Theme.getColor("text")
                renderType: Text.NativeRendering
            }

             Item
    {
        height: 50
        width: 250
        anchors.horizontalCenter: parent.horizontalCenter
        TextField
        {
            id: email
            text: emailText
            anchors.horizontalCenter: parent.horizontalCenter
            placeholderText: catalog.i18nc("@text", "Email")
            onEditingFinished: {
                if (text != "") emailErrorVisible = false
                else emailErrorVisible = true
            }
        }
        Label
        {
            id: emailError
            anchors.left: email.left
            anchors.top: email.bottom
            horizontalAlignment: Text.AlignLeft
            text: catalog.i18nc("@text", "Email is required")
            color: "red"
            visible: emailErrorVisible
        }
    }

    Item
    {
        height: 50
        width: 50
        anchors.horizontalCenter: parent.horizontalCenter
        TextField
        {
            id: password
            text: passwordText
            anchors.horizontalCenter: parent.horizontalCenter
            placeholderText: catalog.i18nc("@text", "Password")
            echoMode: TextInput.Password
            onEditingFinished: {
                if (text != "") passwordErrorVisible = false
                else passwordErrorVisible = true
            }
        }
        Label
        {
            id: passwordError
            anchors.left: password.left
            anchors.top: password.bottom
            horizontalAlignment: Text.AlignLeft
            text: catalog.i18nc("@text", "Password is required")
            color: "red"
            visible: passwordErrorVisible
        }
    }

    Item
    {
        height: 12
        width: 50
        anchors.horizontalCenter: parent.horizontalCenter
        Label {
            anchors.horizontalCenter: parent.horizontalCenter
            text: signInStatusCode == 400 || signInStatusCode == 401 ? catalog.i18nc("@text", "Incorrect email or password") : signInStatusCode == -1 ? catalog.i18nc("@text", "Can't sign in. Check internet connection") : signInStatusCode == -2 ? catalog.i18nc("@text", "Can't sign in. Error loading api data"): catalog.i18nc("@text", "Can't sign in. Something went wrong")
            color: "red"
            visible: signInStatusCode != 200
        }
    }

    Cura.PrimaryButton
    {
        anchors.horizontalCenter: parent.horizontalCenter
        width: UM.Theme.getSize("account_button").width
        height: UM.Theme.getSize("account_button").height
        text: catalog.i18nc("@button", "Sign in")
        onClicked: {
        signInStatusCode = Cura.AuthenticationService.signIn(email.text, password.text)
            if(signInStatusCode == 200) {
                base.showNextPage()
            }

        }
        fixedWidthMode: true

    }

        Cura.SecondaryButton
        {
            anchors.horizontalCenter: parent.horizontalCenter
            width: UM.Theme.getSize("account_button").width
            height: UM.Theme.getSize("account_button").height
            text: catalog.i18nc("@button", "Create account")
            onClicked: Qt.openUrlExternally("https://cloud.bcn3d.com")
            fixedWidthMode: true
        }


        }


    }


    // The "Skip" button exists on the bottom right
    Label
    {
        id: skipButton
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
