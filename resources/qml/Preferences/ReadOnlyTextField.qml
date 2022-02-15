// Copyright (c) 2016 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.
// Different than the name suggests, it is not always read-only.

import QtQuick 2.1
import QtQuick.Controls 2.1
import UM 1.5 as UM

Item
{
    id: base

    property alias text: textField.text

    signal editingFinished();

    property bool readOnly: false

    width: textField.width
    height: textField.height

    TextField
    {
        id: textField

        enabled: !base.readOnly

        color: UM.Theme.getColor("text")
        font: UM.Theme.getFont("default")
        anchors.fill: parent

        onEditingFinished: base.editingFinished()
        Keys.onEnterPressed: base.editingFinished()
        Keys.onReturnPressed: base.editingFinished()
        background: Rectangle
        {
            radius: UM.Theme.getSize("setting_control_radius").width
            color: textField.enabled ? UM.Theme.getColor("setting_control") : UM.Theme.getColor("setting_control_disabled")
        }
    }
}
