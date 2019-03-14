// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 2.0
import QtQuick.Controls.Styles 1.4
import UM 1.3 as UM

Button {
    background: Rectangle {
        opacity: parent.down || parent.hovered ? 1 : 0;
        color: UM.Theme.getColor("monitor_context_menu_hover")
    }
    contentItem: Label {
        color: enabled ? UM.Theme.getColor("monitor_text_primary") : UM.Theme.getColor("monitor_text_disabled");
        text: parent.text
        horizontalAlignment: Text.AlignLeft;
        verticalAlignment: Text.AlignVCenter;
    }
    height: visible ? 39 * screenScaleFactor : 0; // TODO: Theme!
    hoverEnabled: true;
    width: parent.width;
}