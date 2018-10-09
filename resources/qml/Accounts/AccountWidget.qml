// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1

import UM 1.4 as UM
import Cura 1.1 as Cura

Item
{
    id: accountWidget
    property var profile: Cura.API.account.userProfile
    property var loggedIn: Cura.API.account.isLoggedIn
    property var logoutCallback: Cura.API.account.logout
    height: UM.Theme.getSize("topheader").height
    width: UM.Theme.getSize("topheader").height

    AvatarImage
    {
        id: avatar
        width: Math.round(0.8 * parent.width)
        height: Math.round(0.8 * parent.height)
        anchors.verticalCenter: parent.verticalCenter
        anchors.horizontalCenter: parent.horizontalCenter
        source: loggedIn ? profile["profile_image_url"] : UM.Theme.getImage("avatar_default")
    }

    MouseArea
    {
        anchors.fill: parent
        onClicked: accountManagementPanel.visible = !accountManagementPanel.visible // Collapse/Expand the dropdown panel
    }

    UM.PointingRectangle
    {
        id: accountManagementPanel

        width: panel.width
        height: panel.height

        anchors
        {
            top: parent.bottom
            topMargin: UM.Theme.getSize("default_margin").height
            right: parent.right
        }

        target: Qt.point(parent.width / 2, parent.bottom)
        arrowSize: UM.Theme.getSize("default_arrow").width

        visible: false
        opacity: visible ? 1 : 0
        Behavior on opacity { NumberAnimation { duration: 100 } }

        color: UM.Theme.getColor("tool_panel_background")
        borderColor: UM.Theme.getColor("lining")
        borderWidth: UM.Theme.getSize("default_lining").width

        // Shows the user management options or general options to create account
        Loader
        {
            id: panel
            sourceComponent: loggedIn ? userManagementWidget : generalManagementWidget
        }
    }

    Component
    {
        id: userManagementWidget
        UserManagementWidget { }
    }

    Component
    {
        id: generalManagementWidget
        GeneralManagementWidget { }
    }
}