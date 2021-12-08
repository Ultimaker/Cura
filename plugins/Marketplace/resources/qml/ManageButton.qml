// Copyright (c) 2021 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.1

import UM 1.6 as UM
import Cura 1.6 as Cura

RowLayout
{
    id: manageButton
    property string button_style
    property string primaryText
    property string secondaryText
    property string busyPrimaryText
    property string busySecondaryText
    property string confirmedPrimaryText
    property string confirmedSecondaryText
    property bool confirmedTextChoice: true

    signal clicked(bool primary_action)

    property Component primaryButton: Component
    {
        Cura.PrimaryButton
        {
            id: primaryButton
            enabled: manageButton.enabled
            text: manageButton.primaryText

            onClicked:
            {
                manageButton.confirmedTextChoice = true
                manageButton.clicked(true)
            }
        }
    }

    property Component secondaryButton: Component
    {
        Cura.SecondaryButton
        {
            id: secondaryButton
            enabled: manageButton.enabled
            text: manageButton.secondaryText

            onClicked:
            {
                manageButton.confirmedTextChoice = false
                manageButton.clicked(false)
            }
        }
    }

    property Component busyButton: Component
    {
        Item
        {
            id: busyMessage
            height: UM.Theme.getSize("action_button").height
            width: childrenRect.width

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
                text: manageButton.busyMessageText

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
                text: manageButton.confirmedTextChoice ? manageButton.confirmedPrimaryText : manageButton.confirmedSecondaryText

                font: UM.Theme.getFont("medium_bold")
                color: UM.Theme.getColor("primary")
            }
        }
    }

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
