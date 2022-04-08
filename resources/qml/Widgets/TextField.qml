// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.5 as UM
import Cura 1.1 as Cura


//
// Cura-style TextField
//
TextField
{
    id: control

    property alias leftIcon: iconLeft.source

    height: UM.Theme.getSize("setting_control").height

    hoverEnabled: true
    selectByMouse: true
    font: UM.Theme.getFont("default")
    color: UM.Theme.getColor("text_field_text")
    renderType: Text.NativeRendering
    selectionColor: UM.Theme.getColor("text_selection")
    leftPadding: iconLeft.visible ? iconLeft.width + UM.Theme.getSize("default_margin").width * 2 : UM.Theme.getSize("thin_margin").width

    states: [
        State
        {
            name: "disabled"
            when: !control.enabled
            PropertyChanges { target: control; color: UM.Theme.getColor("text_field_text_disabled")}
            PropertyChanges { target: backgroundRectangle; liningColor: UM.Theme.getColor("text_field_border_disabled")}
        },
        State
        {
            name: "invalid"
            when: !control.acceptableInput
            PropertyChanges { target: backgroundRectangle; color: UM.Theme.getColor("setting_validation_error_background")}
        },
        State
        {
            name: "hovered"
            when: control.hovered || control.activeFocus
            PropertyChanges { target: backgroundRectangle; liningColor: UM.Theme.getColor("text_field_border_hovered")}
        }
    ]

    background: UM.UnderlineBackground
    {
        id: backgroundRectangle
        //Optional icon added on the left hand side.
        UM.ColorImage
        {
            id: iconLeft

            anchors
            {
                verticalCenter: parent.verticalCenter
                left: parent.left
                leftMargin: UM.Theme.getSize("default_margin").width
            }

            visible: source != ""
            height: UM.Theme.getSize("small_button_icon").height
            width: visible ? height : 0
            color: control.color
        }
    }
}
