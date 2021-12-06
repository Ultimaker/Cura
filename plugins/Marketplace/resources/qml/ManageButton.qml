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
    property alias primaryText: primaryButton.text
    property alias secondaryText: secondaryButton.text
    property string busyPrimaryText: busyMessageText.text
    property string busySecondaryText: busyMessageText.text
    property bool enabled: true
    property bool busy: state == "busy"

    signal clicked(bool primary_action)

    Cura.PrimaryButton
    {
        id: primaryButton
        visible: false
        enabled: manageButton.enabled

        onClicked:
        {
            manageButton.clicked(true)
        }
    }

    Cura.SecondaryButton
    {
        id: secondaryButton
        visible: false
        enabled: manageButton.enabled

        onClicked:
        {
            manageButton.clicked(false)
        }
    }

    Item
    {
        id: busyMessage
        visible: false
        height: UM.Theme.getSize("action_button").height
        width: childrenRect.width

        BusyIndicator
        {
            id: busyIndicator
            visible: parent.visible
            width: height
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom

            palette.dark: UM.Theme.getColor("text")

            RotationAnimator
            {
                target: busyIndicator.contentItem
                running: busyIndicator.visible && busyIndicator.running
                from: 0
                to: 360
                loops: Animation.Infinite
                duration: 2500
            }
        }
        Label
        {
            id: busyMessageText
            visible: parent.visible
            text: manageButton.state == "primary" ? manageButton.busyPrimaryText : manageButton.busySecondaryText
            anchors.left: busyIndicator.right
            anchors.verticalCenter: parent.verticalCenter

            font: UM.Theme.getFont("default")
            color: UM.Theme.getColor("text")
        }
    }

    states:
    [
        State
        {
            name: "primary"
            PropertyChanges
            {
                target: primaryButton
                visible: true
            }
            PropertyChanges
            {
                target: secondaryButton
                visible: false
            }
            PropertyChanges
            {
                target: busyMessage
                visible: false
            }
        },
        State
        {
            name: "secondary"
            PropertyChanges
            {
                target: primaryButton
                visible: false
            }
            PropertyChanges
            {
                target: secondaryButton
                visible: true
            }
            PropertyChanges
            {
                target: busyMessage
                visible: false
            }
        },
        State
        {
            name: "hidden"
            PropertyChanges
            {
                target: manageButton
                visible: false
            }
        },
        State
        {
            name: "busy"
            PropertyChanges
            {
                target: primaryButton
                visible: false
            }
            PropertyChanges
            {
                target: secondaryButton
                visible: false
            }
            PropertyChanges
            {
                target: busyMessage
                visible: manageButton.visible
            }
        }
    ]
}
