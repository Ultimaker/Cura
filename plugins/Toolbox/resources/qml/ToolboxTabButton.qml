// Copyright (c) 2018 Ultimaker B.V.
// Toolbox is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import UM 1.1 as UM

Button
{
    property bool active: false
    style: ButtonStyle
    {
        background: Rectangle
        {
            color: "transparent"
            implicitWidth: UM.Theme.getSize("toolbox_header_tab").width
            implicitHeight: UM.Theme.getSize("toolbox_header_tab").height
            Rectangle
            {
                visible: control.active
                color: UM.Theme.getColor("sidebar_header_highlight_hover")
                anchors.bottom: parent.bottom
                width: parent.width
                height: UM.Theme.getSize("sidebar_header_highlight").height
            }
        }
        label: Label
        {
            text: control.text
            color:
            {
                if(control.hovered)
                {
                    return UM.Theme.getColor("topbar_button_text_hovered");
                }
                if(control.active)
                {
                    return UM.Theme.getColor("topbar_button_text_active");
                }
                else
                {
                    return UM.Theme.getColor("topbar_button_text_inactive");
                }
            }
            font: control.enabled ? (control.active ? UM.Theme.getFont("medium_bold") : UM.Theme.getFont("medium")) : UM.Theme.getFont("default_italic")
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
        }
    }
}
