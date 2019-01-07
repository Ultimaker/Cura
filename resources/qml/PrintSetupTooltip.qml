// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.3

import UM 1.0 as UM

UM.PointingRectangle {
    id: base;

    width: UM.Theme.getSize("tooltip").width;
    height: label.height + UM.Theme.getSize("tooltip_margins").height * 2;
    color: UM.Theme.getColor("tooltip");

    arrowSize: UM.Theme.getSize("default_arrow").width

    opacity: 0;
    Behavior on opacity { NumberAnimation { duration: 100; } }

    property alias text: label.text;

    function show(position) {
        if(position.y + base.height > parent.height) {
            x = position.x - base.width;
            y = parent.height - base.height;
        } else {
            x = position.x - base.width;
            y = position.y - UM.Theme.getSize("tooltip_arrow_margins").height;
            if(y < 0)
            {
                position.y += -y;
                y = 0;
            }
        }
        base.opacity = 1;
        target = Qt.point(position.x + 1, position.y + Math.round(UM.Theme.getSize("tooltip_arrow_margins").height / 2))
    }

    function hide() {
        base.opacity = 0;
    }

    Label
    {
        id: label;
        anchors {
            top: parent.top;
            topMargin: UM.Theme.getSize("tooltip_margins").height;
            left: parent.left;
            leftMargin: UM.Theme.getSize("tooltip_margins").width;
            right: parent.right;
            rightMargin: UM.Theme.getSize("tooltip_margins").width;
        }
        wrapMode: Text.Wrap;
        textFormat: Text.RichText
        font: UM.Theme.getFont("default");
        color: UM.Theme.getColor("tooltip_text");
        renderType: Text.NativeRendering
    }
}
