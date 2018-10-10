// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.1

import UM 1.4 as UM
import Cura 1.1 as Cura

import "../components"

Column
{
    property var profile: null
    property var loggedIn: false

    padding: 2 * UM.Theme.getSize("default_margin").height
    spacing: 2 * UM.Theme.getSize("default_margin").height

    AvatarImage
    {
        id: avatar
        width: 75 * screenScaleFactor
        height: 75 * screenScaleFactor
        anchors.horizontalCenter: parent.horizontalCenter
        source: loggedIn ? profile["profile_image_url"] : UM.Theme.getImage("avatar_default")
        outlineColor: loggedIn ? UM.Theme.getColor("account_widget_ouline_active") : UM.Theme.getColor("account_widget_ouline_inactive")
    }

    Label
    {
        id: message
        anchors.horizontalCenter: parent.horizontalCenter
        visible: !loggedIn
        text: catalog.i18nc("@label", "Please login or create an account to  enjoy all features of Ultimaker Cura")
    }

    Column
    {
        id: userInformation
        anchors.horizontalCenter: parent.horizontalCenter
        visible: loggedIn

        Label
        {
            anchors.horizontalCenter: parent.horizontalCenter
            text: loggedIn ? profile["username"] : ""
            font: UM.Theme.getFont("large")
        }

        Label
        {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "email.address@hardcoded.is"
            font: UM.Theme.getFont("default")
        }
    }

    Loader
    {
        id: accountEntryPoints
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