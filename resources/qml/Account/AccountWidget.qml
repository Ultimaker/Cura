// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.4 as UM
import Cura 1.1 as Cura

Item
{
    property var profile: Cura.API.account.userProfile
    property var loggedIn: Cura.API.account.isLoggedIn

    height: signInButton.visible ? signInButton.height : accountWidget.height
    width: signInButton.visible ? signInButton.width : accountWidget.width

    Button
    {
        id: signInButton

        anchors.verticalCenter: parent.verticalCenter

        text: catalog.i18nc("@action:button", "Sign in")

        height: Math.round(0.5 * UM.Theme.getSize("main_window_header").height)
        onClicked: popup.opened ? popup.close() : popup.open()
        visible: !loggedIn

        hoverEnabled: true

        background: Rectangle
        {
            radius: UM.Theme.getSize("action_button_radius").width
            color: UM.Theme.getColor("main_window_header_background")
            border.width: UM.Theme.getSize("default_lining").width
            border.color: UM.Theme.getColor("primary_text")

            Rectangle
            {
                anchors.fill: parent
                radius: parent.radius
                color: UM.Theme.getColor("primary_text")
                opacity: signInButton.hovered ? 0.2 : 0
                Behavior on opacity { NumberAnimation { duration: 100 } }
            }
        }

        contentItem: Label
        {
            id: label
            text: signInButton.text
            font: UM.Theme.getFont("default")
            color: UM.Theme.getColor("primary_text")
            width: contentWidth
            verticalAlignment: Text.AlignVCenter
            renderType: Text.NativeRendering
        }
    }

    Button
    {
        id: accountWidget

        anchors.verticalCenter: parent.verticalCenter

        implicitHeight: Math.round(0.5 * UM.Theme.getSize("main_window_header").height)
        implicitWidth: Math.round(0.5 * UM.Theme.getSize("main_window_header").height)

        hoverEnabled: true

        visible: loggedIn

        text: (loggedIn && profile["profile_image_url"] == "") ? profile["username"].charAt(0).toUpperCase() : ""

        background: AvatarImage
        {
            id: avatar

            width: accountWidget.width
            height: accountWidget.height
            anchors.verticalCenter: accountWidget.verticalCenter
            anchors.horizontalCenter: accountWidget.horizontalCenter

            source: (loggedIn && profile["profile_image_url"]) ? profile["profile_image_url"] : ""
            outlineColor: loggedIn ? UM.Theme.getColor("account_widget_outline_active") : UM.Theme.getColor("lining")
        }

        contentItem: Item
        {
            anchors.verticalCenter: accountWidget.verticalCenter
            anchors.horizontalCenter: accountWidget.horizontalCenter
            visible: avatar.source == ""
            Rectangle
            {
                id: initialCircle
                anchors.centerIn: parent
                width: Math.min(accountWidget.width, accountWidget.height)
                height: width
                radius: width
                color: UM.Theme.getColor("main_window_header_background")
                border.width: UM.Theme.getSize("default_lining").width
                border.color: UM.Theme.getColor("primary_text")

                Rectangle
                {
                    id: initialCircleFill
                    anchors.fill: parent
                    radius: parent.radius
                    color: UM.Theme.getColor("primary_text")
                    opacity: accountWidget.hovered ? 0.2 : 0
                    Behavior on opacity { NumberAnimation { duration: 100 } }
                }
            }

            Label
            {
                id: initialLabel
                anchors.verticalCenter: parent.verticalCenter
                anchors.horizontalCenter: parent.horizontalCenter
                text: accountWidget.text
                font: UM.Theme.getFont("large_bold")
                color: UM.Theme.getColor("primary_text")
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
                renderType: Text.NativeRendering
            }
        }

        onClicked: {
            if (popup.opened)
            {
                popup.close()
            } else {
                Cura.API.account.popupOpened()
                popup.open()
            }
        }
    }

    Popup
    {
        id: popup

        y: parent.height + UM.Theme.getSize("default_arrow").height
        x: parent.width - width

        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutsideParent
        onOpened: Cura.API.account.popupOpened()

        opacity: opened ? 1 : 0
        Behavior on opacity { NumberAnimation { duration: 100 } }
        padding: 0
        contentItem: AccountDetails
        {}

        background: UM.PointingRectangle
        {
            color: UM.Theme.getColor("tool_panel_background")
            borderColor: UM.Theme.getColor("lining")
            borderWidth: UM.Theme.getSize("default_lining").width

            target: Qt.point(width - ((signInButton.visible ? signInButton.width : accountWidget.width) / 2), -10)

            arrowSize: UM.Theme.getSize("default_arrow").width
        }
    }
}
