// Copyright (c) 2016 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.1
import QtQuick.Controls 2.15

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
        opacity: base.readOnly ? 0.5 : 1.0
        selectByMouse: true

        background: Rectangle
        {
            radius: UM.Theme.getSize("setting_control_radius").width
            color: enabled ? UM.Theme.getColor("setting_control_disabled") : UM.Theme.getColor("setting_control")
        }

        color: UM.Theme.getColor("text")
        font: UM.Theme.getFont("default")

        Keys.onReturnPressed:
        {
            base.editingFinished()
        }

        Keys.onEnterPressed:
        {
            base.editingFinished()
        }

        onActiveFocusChanged:
        {
            if(!activeFocus)
            {
                base.editingFinished()
            }
        }
    }
}
