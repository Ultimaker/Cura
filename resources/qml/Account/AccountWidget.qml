// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.1

import UM 1.4 as UM
import Cura 1.1 as Cura

Button
{
    id: accountWidget
    property var profile: Cura.API.account.userProfile
    property var loggedIn: Cura.API.account.isLoggedIn

    implicitHeight: UM.Theme.getSize("main_window_header").height
    implicitWidth: UM.Theme.getSize("main_window_header").height

    AvatarImage
    {
        id: avatar

        width: Math.round(0.8 * parent.width)
        height: Math.round(0.8 * parent.height)
        anchors.verticalCenter: parent.verticalCenter
        anchors.horizontalCenter: parent.horizontalCenter

        source: loggedIn ? profile["profile_image_url"] : UM.Theme.getImage("avatar_no_user")
        outlineColor: loggedIn ? UM.Theme.getColor("account_widget_outline_active") : UM.Theme.getColor("account_widget_outline_inactive")
    }

    background: Item {}

    onClicked: popup.opened ? popup.close() : popup.open()

    Popup
    {
        id: popup

        y: parent.height + UM.Theme.getSize("default_arrow").height
        x: parent.width - width

        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutsideParent

        contentItem: AccountDetails
        {
            id: panel
            profile: Cura.API.account.userProfile
            loggedIn: Cura.API.account.isLoggedIn
        }

        background: UM.PointingRectangle
        {
            opacity: visible ? 1 : 0
            Behavior on opacity { NumberAnimation { duration: 100 } }
            color: UM.Theme.getColor("tool_panel_background")
            borderColor: UM.Theme.getColor("lining")
            borderWidth: UM.Theme.getSize("default_lining").width

            target: Qt.point(width - (accountWidget.width / 2), -10)

            arrowSize: UM.Theme.getSize("default_arrow").width
        }
    }
}
