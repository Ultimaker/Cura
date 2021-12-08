// Copyright (c) 2021 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.1

import UM 1.6 as UM
import Cura 1.6 as Cura

Item
{
    id: manageButton
    property string button_style
    property string text
    property bool busy
    property bool confirmed

    signal clicked(bool primary_action)

    property Component primaryButton: Component
    {
        Cura.PrimaryButton
        {
            id: primaryButton
            text: manageButton.text

            onClicked:
            {
                manageButton.clicked(true)
            }
        }
    }

    property Component secondaryButton: Component
    {
        Cura.SecondaryButton
        {
            id: secondaryButton
            text: manageButton.text

            onClicked:
            {
                manageButton.clicked(false)
            }
        }
    }

    property Component busyButton: Component
    {
        Item
        {
            id: busyMessage

            UM.RecolorImage
            {
                id: busyIndicator
                width: height
                anchors.left: parent.left
                anchors.top: parent.top
                anchors.topMargin: UM.Theme.getSize("narrow_margin").height
                anchors.bottom: parent.bottom
                anchors.bottomMargin: anchors.topMargin

                source: UM.Theme.getIcon("Spinner")
                color: UM.Theme.getColor("primary")

                RotationAnimator
                {
                    target: busyIndicator
                    running: busyMessage.visible
                    from: 0
                    to: 360
                    loops: Animation.Infinite
                    duration: 2500
                }
            }
            Label
            {
                id: busyMessageText
                anchors.left: busyIndicator.right
                anchors.leftMargin: UM.Theme.getSize("narrow_margin").width
                anchors.verticalCenter: parent.verticalCenter
                text: manageButton.text

                font: UM.Theme.getFont("medium_bold")
                color: UM.Theme.getColor("primary")
            }
        }
    }

    property Component confirmButton: Component
    {
        Item
        {

            height: UM.Theme.getSize("action_button").height
            width: childrenRect.width

            Label
            {
                id: confirmedMessageText
                anchors.verticalCenter: parent.verticalCenter
                text: manageButton.text

                font: UM.Theme.getFont("medium_bold")
                color: UM.Theme.getColor("primary")
            }
        }
    }

    height: UM.Theme.getSize("action_button").height
    width: childrenRect.width

    Loader
    {

        sourceComponent:
        {
            switch (manageButton.button_style)
            {
                case "primary":
                    return manageButton.primaryButton;
                case "secondary":
                    return manageButton.secondaryButton;
                case "busy":
                    return manageButton.busyButton;
                case "confirmed":
                    return manageButton.confirmButton;
                default:
                    return;
            }
        }
    }
}
