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
    property string confirmedPrimaryText: confirmedMessageText.text
    property string confirmedSecondaryText: confirmedMessageText.text
    property bool busy
    property bool confirmed
    property bool confirmedTextChoice: true

    signal clicked(bool primary_action)

    Cura.PrimaryButton
    {
        id: primaryButton
        enabled: manageButton.enabled

        onClicked:
        {
            busyMessage.text = manageButton.busyPrimaryText
            confirmedMessage.text = manageButton.confirmedPrimaryText
            manageButton.clicked(true)
        }
    }

    Cura.SecondaryButton
    {
        id: secondaryButton
        enabled: manageButton.enabled

        onClicked:
        {
            busyMessage.text = manageButton.busySecondaryText
            confirmedMessage.text = manageButton.confirmedSecondaryText
            manageButton.clicked(false)
        }
    }

    Item
    {
        id: busyMessage
        property alias text: busyMessageText.text
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

            font: UM.Theme.getFont("medium_bold")
            color: UM.Theme.getColor("primary")
        }
    }

    Item
    {
        id: confirmedMessage
        property alias text: confirmedMessageText.text

        height: UM.Theme.getSize("action_button").height
        width: childrenRect.width

        Label
        {
            id: confirmedMessageText
            anchors.verticalCenter: parent.verticalCenter

            font: UM.Theme.getFont("medium_bold")
            color: UM.Theme.getColor("primary")
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
            PropertyChanges
            {
                target: confirmedMessage
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
            PropertyChanges
            {
                target: confirmedMessage
                visible: false
            }
        },
        State
        {
            name: "hidden"
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
                visible: false
            }
            PropertyChanges
            {
                target: confirmedMessage
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
                visible: true
            }
            PropertyChanges
            {
                target: confirmedMessage
                visible: false
            }
        },
        State
        {
            name: "confirmed"
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
                visible: false
            }
            PropertyChanges
            {
                target: confirmedMessage
                visible: true
                text: manageButton.confirmedTextChoice ? manageButton.confirmedPrimaryText : manageButton.confirmedSecondaryText
            }
        }
    ]
}
