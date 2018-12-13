// Copyright (c) 2018 Ultimaker B.V.
import QtQuick 2.7
import QtQuick.Controls 2.1
import QtQuick.Layouts 1.3

import UM 1.3 as UM

CheckBox
{
    id: checkbox
    hoverEnabled: true

    property var label: ""

    indicator: Rectangle {
        implicitWidth: 30 * screenScaleFactor
        implicitHeight: 30 * screenScaleFactor
        x: 0
        y: Math.round(parent.height / 2 - height / 2)
        color: UM.Theme.getColor("sidebar")
        border.color: UM.Theme.getColor("text")

        Rectangle {
            width: 14 * screenScaleFactor
            height: 14 * screenScaleFactor
            x: 8 * screenScaleFactor
            y: 8 * screenScaleFactor
            color: UM.Theme.getColor("primary")
            visible: checkbox.checked
        }
    }

    contentItem: Label {
        anchors
        {
            left: checkbox.indicator.right
            leftMargin: 5 * screenScaleFactor
        }
        text: catalog.i18nc("@checkbox:description", "Auto Backup")
        color: UM.Theme.getColor("text")
        renderType: Text.NativeRendering
        verticalAlignment: Text.AlignVCenter
    }

    ActionToolTip
    {
        text: checkbox.label
    }
}
