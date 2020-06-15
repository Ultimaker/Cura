// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.4 as UM
import Cura 1.1 as Cura

Column
{
    spacing: UM.Theme.getSize("narrow_margin").height

    Item
    {
        width: childrenRect.width
        height: childrenRect.height
        AvatarImage
        {
            id: avatar

            width: UM.Theme.getSize("main_window_header").height
            height: UM.Theme.getSize("main_window_header").height

            source: profile["profile_image_url"] ? profile["profile_image_url"] : ""
            outlineColor: "transparent"
        }
        Column
        {
            anchors.left: avatar.right
            anchors.leftMargin: UM.Theme.getSize("default_margin").width
            spacing: UM.Theme.getSize("narrow_margin").height
            Label
            {
                id: username
                renderType: Text.NativeRendering
                text: profile.username
                font: UM.Theme.getFont("large_bold")
                color: UM.Theme.getColor("text")
            }

            SyncState
            {
                id: syncRow
            }
            Label
            {
                id: lastSyncLabel
                renderType: Text.NativeRendering
                text: catalog.i18nc("@label The argument is a timestamp", "Last update: %1").arg(Cura.API.account.lastSyncDateTime)
                font: UM.Theme.getFont("default")
                color: UM.Theme.getColor("text_medium")
            }
        }
    }

    Rectangle
    {
        width: parent.width
        color: UM.Theme.getColor("lining")
        height: UM.Theme.getSize("default_lining").height
    }
    Cura.TertiaryButton
    {
        id: cloudButton
        width: UM.Theme.getSize("account_button").width
        height: UM.Theme.getSize("account_button").height
        text: catalog.i18nc("@button", "Ultimaker Digital Factory")
        onClicked: Qt.openUrlExternally(CuraApplication.ultimakerDigitalFactoryUrl)
        fixedWidthMode: false
    }

    Cura.TertiaryButton
    {
        id: accountButton
        width: UM.Theme.getSize("account_button").width
        height: UM.Theme.getSize("account_button").height
        text: catalog.i18nc("@button", "Ultimaker Account")
        onClicked: Qt.openUrlExternally(CuraApplication.ultimakerCloudAccountRootUrl)
        fixedWidthMode: false
    }

    Rectangle
    {
        width: parent.width
        color: UM.Theme.getColor("lining")
        height: UM.Theme.getSize("default_lining").height
    }

    Cura.TertiaryButton
    {
        id: signOutButton
        onClicked: Cura.API.account.logout()
        text: catalog.i18nc("@button", "Sign Out")
    }
}
