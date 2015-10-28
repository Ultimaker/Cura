// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1

import UM 1.0 as UM

Rectangle {
    id: base;

    width: UM.Theme.sizes.tooltip.width;
    height: label.height + UM.Theme.sizes.tooltip_margins.height * 2;
    color: UM.Theme.colors.tooltip;

    opacity: 0;
    Behavior on opacity { NumberAnimation { duration: 100; } }

    property alias text: label.text;

    function show(position) {
        if(position.y + base.height > parent.height) {
            x = position.x - base.width;
            y = parent.height - base.height;
        } else {
            x = position.x - base.width;
            y = position.y;
        }
        base.opacity = 1;
    }

    function hide() {
        base.opacity = 0;
    }

    Label {
        id: label;
        anchors {
            top: parent.top;
            topMargin: UM.Theme.sizes.tooltip_margins.height;
            left: parent.left;
            leftMargin: UM.Theme.sizes.tooltip_margins.width;
            right: parent.right;
            rightMargin: UM.Theme.sizes.tooltip_margins.width;
        }
        wrapMode: Text.Wrap;
        font: UM.Theme.fonts.default;
        color: UM.Theme.colors.text_default;
    }
}
