// Copyright (c) 2022 Ultimaker B.V.
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
    id: control

    font: UM.Theme.getFont("default")

    states: [
        State {
            name: "selected-hover"
            when: control.enabled && control.checked && control.hovered
            PropertyChanges
            {
                target: indicator_background
                color: UM.Theme.getColor("radio_selected")
                border.color: UM.Theme.getColor("radio_border_hover")
            }
        },
        State {
            name: "selected"
            when: control.enabled && control.checked
            PropertyChanges
            {
                target: indicator_background
                color: UM.Theme.getColor("radio_selected")
            }
        },
        State {
            name: "hovered"
            when: control.enabled && control.hovered
            PropertyChanges
            {
                target: indicator_background
                border.color: UM.Theme.getColor("radio_border_hover")
            }
        },
        State {
            name: "selected_disabled"
            when: !control.enabled && control.checked
            PropertyChanges
            {
                target: indicator_background
                color: UM.Theme.getColor("radio_selected_disabled")
                border.color: UM.Theme.getColor("radio_border_disabled")
            }
        },
        State {
            name: "disabled"
            when: !control.enabled
            PropertyChanges
            {
                target: indicator_background
                color: UM.Theme.getColor("radio_disabled")
                border.color: UM.Theme.getColor("radio_border_disabled")
            }
        }
    ]

    background: Item
    {
        anchors.fill: parent
    }

    indicator: Rectangle
    {
        id: indicator_background
        implicitWidth: UM.Theme.getSize("radio_button").width
        implicitHeight: UM.Theme.getSize("radio_button").height
        anchors.verticalCenter: parent.verticalCenter
        anchors.alignWhenCentered: false
        radius: width / 2
        color: UM.Theme.getColor("radio")
        border.width: UM.Theme.getSize("default_lining").width
        border.color: UM.Theme.getColor("radio_border")

        Rectangle
        {
            id: indicator_dot
            width: (parent.width / 2) | 0
            height: width
            anchors.centerIn: parent
            radius: width / 2
            color: control.enabled ? UM.Theme.getColor("radio_dot") : UM.Theme.getColor("radio_dot_disabled")
            visible: control.checked


        }
    }

    contentItem: UM.Label
    {
        leftPadding: control.indicator.width + control.spacing
        text: control.text
        font: control.font
        color: control.enabled ? UM.Theme.getColor("radio_text"): UM.Theme.getColor("radio_text_disabled")
    }
}
