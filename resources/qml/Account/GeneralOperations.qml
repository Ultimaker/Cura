// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.4 as UM
import Cura 1.1 as Cura

Column
{
    spacing: UM.Theme.getSize("default_margin").width

    Image
    {
        id: machinesImage
        anchors.horizontalCenter: parent.horizontalCenter
        source: UM.Theme.getIcon("sign_in_to_cloud")
        horizontalAlignment: Image.AlignHCenter
        verticalAlignment: Image.AlignVCenter
    }

    Label
    {
        id: title
        anchors.horizontalCenter: parent.horizontalCenter
        horizontalAlignment: Text.AlignHCenter
        renderType: Text.NativeRendering
        text: catalog.i18nc("@label", "Ultimaker Cloud")
        font: UM.Theme.getFont("large_bold")
        color: UM.Theme.getColor("text")
    }

    Label
    {
        id: generalInformation
        anchors.horizontalCenter: parent.horizontalCenter
        horizontalAlignment: Text.AlignHCenter
        renderType: Text.NativeRendering
        text: catalog.i18nc("@label", "Enjoy a more powerful 3D printing experience.")
        font: UM.Theme.getFont("default")
        color: UM.Theme.getColor("text")
    }

    Label
    {
        id: generalInformationPoints
        anchors.horizontalCenter: parent.horizontalCenter
        horizontalAlignment: Text.AlignLeft
        renderType: Text.NativeRendering
        text: {
            var t = " - Send prints to your Ultimaker printer from anywhere\n"
                  + " - Access your Ultimaker Cura Settings worldwide\n"
                  + " - Enhance your workflow with advanced material profiles"
            return catalog.i18nc("@label", t)
        }
        lineHeight: 1.4
        font: UM.Theme.getFont("default")
        color: UM.Theme.getColor("text")
    }

    // placeholder
    Label
    {
        text: " "
    }

    Cura.PrimaryButton
    {
        anchors.horizontalCenter: parent.horizontalCenter
        width: UM.Theme.getSize("account_button").width
        height: UM.Theme.getSize("account_button").height
        text: catalog.i18nc("@button", "Sign in")
        onClicked: Cura.API.account.login()
        fixedWidthMode: true
    }

    Cura.SecondaryButton
    {
        anchors.horizontalCenter: parent.horizontalCenter
        width: UM.Theme.getSize("account_button").width
        height: UM.Theme.getSize("account_button").height
        text: catalog.i18nc("@button", "Create account")
        onClicked: Qt.openUrlExternally(CuraApplication.ultimakerCloudAccountRootUrl + "/app/create")
        fixedWidthMode: true
    }
}