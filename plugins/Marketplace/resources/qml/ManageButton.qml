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
    property bool button_style: true
    property string text
    property bool busy: false
    property bool confirmed: false

    implicitWidth: childrenRect.width
    implicitHeight: childrenRect.height

    signal clicked()

    property Component primaryButton: Component
    {
        Cura.PrimaryButton
        {
            text: manageButton.text
            onClicked: manageButton.clicked()
        }
    }

    property Component secondaryButton: Component
    {
        Cura.SecondaryButton
        {
            text: manageButton.text
            onClicked: manageButton.clicked()
        }
    }

    property Component busyButton: Component
    {
        Item
        {
            height: UM.Theme.getSize("action_button").height
            width: childrenRect.width

            UM.RecolorImage
            {
                id: busyIndicator
                visible: parent.visible
                height: UM.Theme.getSize("action_button").height - 2 * UM.Theme.getSize("narrow_margin").height
                width: height
                anchors.left: parent.left
                anchors.verticalCenter: parent.verticalCenter

                source: UM.Theme.getIcon("Spinner")
                color: UM.Theme.getColor("primary")

                RotationAnimator
                {
                    target: busyIndicator
                    running: parent.visible
                    from: 0
                    to: 360
                    loops: Animation.Infinite
                    duration: 2500
                }
            }
            Label
            {
                visible: parent.visible
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
                anchors.verticalCenter: parent.verticalCenter
                text: manageButton.text

                font: UM.Theme.getFont("medium_bold")
                color: UM.Theme.getColor("primary")
            }
        }
    }

    Loader
    {

        sourceComponent:
        {
            if (busy) { return manageButton.busyButton; }
            else if (confirmed) { return manageButton.confirmButton; }
            else if (manageButton.button_style) { return manageButton.primaryButton; }
            else { return manageButton.secondaryButton; }
        }
    }
}
