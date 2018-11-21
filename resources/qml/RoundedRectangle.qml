import QtQuick 2.0

import UM 1.2 as UM

// The rounded rectangle works mostly like a regular rectangle, but provides the option to have rounded corners on only one side of the rectangle.
Item
{
    // As per the regular rectangle
    property color color: "transparent"

    // As per regular rectangle
    property int radius: UM.Theme.getSize("default_radius").width

    // On what side should the corners be shown 0 can be used if no radius is needed.
    // 1 is down, 2 is left, 3 is up and 4 is right.
    property int cornerSide: 0

    Rectangle
    {
        id: background
        anchors.fill: parent
        radius: cornerSide != 0 ? parent.radius : 0
        color: parent.color
    }

    // The item that covers 2 of the corners to make them not rounded.
    Rectangle
    {
        visible: cornerSide != 0
        height: cornerSide % 2 ? parent.radius: parent.height
        width: cornerSide % 2 ? parent.width : parent.radius
        color: parent.color
        anchors
        {
            right: cornerSide == 2 ? parent.right: undefined
            bottom: cornerSide == 3 ? parent.bottom: undefined
        }
    }
}
