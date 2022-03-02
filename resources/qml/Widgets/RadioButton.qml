// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.5 as UM
import Cura 1.0 as Cura


//
// Cura-style RadioButton.
//
RadioButton
{
    id: radioButton

    font: UM.Theme.getFont("default")

    states: [
        State {
            name: "checked"
            when: radioButton.checked
            PropertyChanges
            {
                target: indicator
                color: UM.Theme.getColor("accent_1")
                border.width: 0
            }
        },
        State
        {
            name: "disabled"
            when: !radioButton.enabled
            PropertyChanges { target: indicator; color: UM.Theme.getColor("background_1")}
        },
        State
        {
            name: "highlighted"
            when: radioButton.hovered || radioButton.activeFocus
            PropertyChanges { target: indicator; border.color: UM.Theme.getColor("border_main_light")}
        }
    ]

    background: Item
    {
        anchors.fill: parent
    }

    indicator: Rectangle
    {
        implicitWidth: UM.Theme.getSize("radio_button").width
        implicitHeight: UM.Theme.getSize("radio_button").height
        anchors.verticalCenter: parent.verticalCenter
        anchors.alignWhenCentered: false
        radius: width / 2
        color: UM.Theme.getColor("background_2")
        border.width: UM.Theme.getSize("default_lining").width
        border.color: UM.Theme.getColor("text_disabled")

        Rectangle
        {
            width: (parent.width / 2) | 0
            height: width
            anchors.centerIn: parent
            radius: width / 2
            color: radioButton.enabled ? UM.Theme.getColor("background_2") : UM.Theme.getColor("background_1")
            visible: radioButton.checked
        }
    }

    contentItem: UM.Label
    {
        leftPadding: radioButton.indicator.width + radioButton.spacing
        text: radioButton.text
        font: radioButton.font
    }
}
