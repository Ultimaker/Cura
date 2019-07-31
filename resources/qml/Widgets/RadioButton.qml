// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.3 as UM
import Cura 1.0 as Cura


//
// Cura-style RadioButton.
//
RadioButton
{
    id: radioButton

    font: UM.Theme.getFont("default")

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
        border.width: UM.Theme.getSize("default_lining").width
        border.color: radioButton.hovered ? UM.Theme.getColor("small_button_text") : UM.Theme.getColor("small_button_text_hover")

        Rectangle
        {
            width: (parent.width / 2) | 0
            height: width
            anchors.centerIn: parent
            radius: width / 2
            color: radioButton.hovered ? UM.Theme.getColor("primary_button_hover") : UM.Theme.getColor("primary_button")
            visible: radioButton.checked
        }
    }

    contentItem: Label
    {
        verticalAlignment: Text.AlignVCenter
        leftPadding: radioButton.indicator.width + radioButton.spacing
        text: radioButton.text
        font: radioButton.font
        color: UM.Theme.getColor("text")
        renderType: Text.NativeRendering
    }
}
