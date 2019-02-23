// Copyright (c) 2018 Ultimaker B.V.
// Toolbox is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import UM 1.1 as UM

Button
{
    id: control
    property bool active: false
    hoverEnabled: true

    background: Item
    {
        implicitWidth: UM.Theme.getSize("toolbox_header_tab").width
        implicitHeight: UM.Theme.getSize("toolbox_header_tab").height
        Rectangle
        {
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
        color:
        {
            if(control.hovered)
            {
                return UM.Theme.getColor("toolbox_header_button_text_hovered");
            }
            if(control.active)
            {
                return UM.Theme.getColor("toolbox_header_button_text_active");
            }
            else
            {
                return UM.Theme.getColor("toolbox_header_button_text_inactive");
            }
        }
        font: control.enabled ? (control.active ? UM.Theme.getFont("medium_bold") : UM.Theme.getFont("medium")) : UM.Theme.getFont("default_italic")
        verticalAlignment: Text.AlignVCenter
        horizontalAlignment: Text.AlignHCenter
        renderType: Text.NativeRendering
    }
}