// Copyright (c) 2018 Ultimaker B.V.
// Toolbox is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import UM 1.1 as UM

ButtonStyle
{
    background: Rectangle
    {
        implicitWidth: UM.Theme.getSize("toolbox_action_button").width
        implicitHeight: UM.Theme.getSize("toolbox_action_button").height
        color: "transparent"
        border
        {
            width: UM.Theme.getSize("default_lining").width
            color: UM.Theme.getColor("lining")
        }
    }
    label: Label
    {
        text: control.text
        color: UM.Theme.getColor("text")
        verticalAlignment: Text.AlignVCenter
        horizontalAlignment: Text.AlignHCenter
    }
}