// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.1

import UM 1.4 as UM
import Cura 1.1 as Cura

Column
{
    property var profile: null
    property var loggedIn: false
    property var profileImage: ""

    padding: UM.Theme.getSize("wide_margin").height
    spacing: UM.Theme.getSize("wide_margin").height

    AvatarImage
    {
        id: avatar
        width: UM.Theme.getSize("avatar_image").width
        height: UM.Theme.getSize("avatar_image").height
        anchors.horizontalCenter: parent.horizontalCenter
        source:
        {
            if(loggedIn)
            {
                if(profileImage)
                {
                    return profileImage
                }
                return UM.Theme.getImage("avatar_no_user")
            }
            return UM.Theme.getImage("avatar_no_user")
        }
        outlineColor: loggedIn ? UM.Theme.getColor("account_widget_outline_active") : UM.Theme.getColor("lining")
    }

    Label
    {
        id: information
        anchors.horizontalCenter: parent.horizontalCenter
        horizontalAlignment: Text.AlignHCenter
        renderType: Text.NativeRendering
        text: loggedIn ? profile["username"] : catalog.i18nc("@label", "Please log in or create an account to\nenjoy all features of Ultimaker Cura.")
        font: loggedIn ? UM.Theme.getFont("large") : UM.Theme.getFont("default")
        color: UM.Theme.getColor("text")
    }

    Loader
    {
        id: accountOperations
        anchors.horizontalCenter: parent.horizontalCenter
        sourceComponent: loggedIn ? userOperations : generalOperations
    }

    Component
    {
        id: userOperations
        UserOperations { }
    }

    Component
    {
        id: generalOperations
        GeneralOperations { }
    }
}