// Copyright (c) 2020 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.3

import UM 1.5 as UM

UM.PointingRectangle
{
    id: base
    property real sourceWidth: 0
    width: UM.Theme.getSize("tooltip").width
    height: textScroll.height + UM.Theme.getSize("tooltip_margins").height
    color: UM.Theme.getColor("tooltip")

    arrowSize: UM.Theme.getSize("default_arrow").width

    opacity: 0
    // This should be disabled when invisible, otherwise it will catch mouse events.
    enabled: opacity > 0

    Behavior on opacity
    {
        NumberAnimation { duration: 200; }
    }

    property alias text: label.text

    function show(position)
    {
        if(position.y + base.height > parent.height)
        {
            x = position.x - base.width;
            y = parent.height - base.height;
        } else
        {
            var new_x = x = position.x - base.width

            // If the tooltip would fall out of the screen, display it on the other side.
            if(new_x < 0)
            {
                new_x = x + sourceWidth + base.width
            }

            x = new_x

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

    function hide()
    {
        base.opacity = 0;
    }

    ScrollView
    {
        id: textScroll
        width: parent.width
        height: Math.min(label.height + UM.Theme.getSize("tooltip_margins").height, base.parent.height)

        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
        ScrollBar.vertical.policy: ScrollBar.AsNeeded

        hoverEnabled: parent.opacity > 0
        onHoveredChanged:
        {
            if(hovered && base.opacity > 0)
            {
                base.show(Qt.point(target.x - 1, target.y - UM.Theme.getSize("tooltip_arrow_margins").height / 2)); //Same arrow position as before.
            }
            else
            {
                base.hide();
            }
        }

        UM.Label
        {
            id: label
            x: UM.Theme.getSize("tooltip_margins").width
            y: UM.Theme.getSize("tooltip_margins").height
            width: textScroll.width - 2 * UM.Theme.getSize("tooltip_margins").width

            textFormat: Text.RichText
            color: UM.Theme.getColor("tooltip_text")
        }
    }
}
