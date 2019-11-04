// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.1
import QtQuick.Window 2.2

import UM 1.3 as UM
import Cura 1.1 as Cura

Column
{
    id: welcomePage
    spacing: UM.Theme.getSize("wide_margin").height
    width: parent.width
    height: childrenRect.height
    anchors.centerIn: parent

    Image
    {
        id: profileImage
        fillMode: Image.PreserveAspectFit
        source: "../../images/logobot.svg"
        anchors.horizontalCenter: parent.horizontalCenter
        width: Math.round(parent.width / 4)
    }

    Label
    {
        id: welcomeTextLabel
        text: catalog.i18nc("@description", "Get plugins and materials verified by Ultimaker")
        width: Math.round(parent.width / 2)
        font: UM.Theme.getFont("default")
        color: UM.Theme.getColor("text")
        verticalAlignment: Text.AlignVCenter
        horizontalAlignment: Text.AlignHCenter
        anchors.horizontalCenter: parent.horizontalCenter
        wrapMode: Label.WordWrap
        renderType: Text.NativeRendering
    }

    Cura.PrimaryButton
    {
        id: loginButton
        width: UM.Theme.getSize("account_button").width
        height: UM.Theme.getSize("account_button").height
        anchors.horizontalCenter: parent.horizontalCenter
        text: catalog.i18nc("@button", "Sign in")
        onClicked: Cura.API.account.login()
        fixedWidthMode: true
    }
}

