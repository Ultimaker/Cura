// Copyright (c) 2016 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.1
import QtQuick.Controls 2.15
import UM 1.5 as UM

ScrollView
{
    id: base

    property alias text: textArea.text
    property alias wrapMode: textArea.wrapMode

    signal editingFinished();

    property bool readOnly: false

    TextArea
    {
        id: textArea

        enabled: !base.readOnly
        selectByMouse: true

        background: Rectangle
        {
            radius: UM.Theme.getSize("setting_control_radius").width
            color: textArea.enabled ? UM.Theme.getColor("setting_control") : UM.Theme.getColor("setting_control_disabled")
        }

        color: UM.Theme.getColor("text")
        font: UM.Theme.getFont("default")

        Keys.onReturnPressed:  base.editingFinished()

        Keys.onEnterPressed: base.editingFinished()

        onActiveFocusChanged:
        {
            if(!activeFocus)
            {
                base.editingFinished()
            }
        }
    }
}
