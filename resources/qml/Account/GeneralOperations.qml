// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.4 as UM
import Cura 1.1 as Cura

Column
{
    spacing: UM.Theme.getSize("default_margin").width
    padding: UM.Theme.getSize("default_margin").width
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
        text: "Ultimaker Account"
        font: UM.Theme.getFont("large_bold")
        color: UM.Theme.getColor("text")
    }

    Label
    {
        id: generalInformation
        anchors.horizontalCenter: parent.horizontalCenter
        horizontalAlignment: Text.AlignHCenter
        renderType: Text.NativeRendering
        text: catalog.i18nc("@label", "Your key to connected 3D printing")
        font: UM.Theme.getFont("default_bold")
        color: UM.Theme.getColor("text")
    }

    Label
    {
        id: generalInformationPoints
        anchors.horizontalCenter: parent.horizontalCenter
        horizontalAlignment: Text.AlignLeft
        renderType: Text.NativeRendering
        text: catalog.i18nc("@text", "- Customize your experience with more print profiles and plugins\n- Stay flexible by syncing your setup and loading it anywhere\n- Increase efficiency with a remote workflow on Ultimaker printers")
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