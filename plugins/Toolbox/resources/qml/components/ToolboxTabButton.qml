// Copyright (c) 2018 Ultimaker B.V.
// Toolbox is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import UM 1.1 as UM

Button
{
    id: control
    property bool active: false

    implicitWidth: UM.Theme.getSize("toolbox_header_tab").width
    implicitHeight: UM.Theme.getSize("toolbox_header_tab").height

    background: Item
    {
        id: backgroundItem
        Rectangle
        {
            id: highlight

            visible: control.active
            color: UM.Theme.getColor("primary")
            anchors.bottom: parent.bottom
            width: parent.width
            height: UM.Theme.getSize("toolbox_header_highlight").height
        }
    }

    contentItem: Label
    {
        id: label
        text: control.text
        color: UM.Theme.getColor("toolbox_header_button_text_inactive")
        font: UM.Theme.getFont("medium")

        verticalAlignment: Text.AlignVCenter
        horizontalAlignment: Text.AlignHCenter

        renderType: Text.NativeRendering
    }

    states:
    [
        State
        {
            name: "disabled"
            when: !control.enabled
            PropertyChanges
            {
                target: label
                font: UM.Theme.getFont("default_italic")
            }
        },
        State
        {
            name: "active"
            when: control.active
            PropertyChanges
            {
                target: label
                font: UM.Theme.getFont("medium_bold")
                color: UM.Theme.getColor("action_button_text")
            }
        }
    ]
}