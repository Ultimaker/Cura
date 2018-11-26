import QtQuick 2.7

import UM 1.2 as UM

// The rounded rectangle works mostly like a regular rectangle, but provides the option to have rounded corners on only one side of the rectangle.
Item
{
    id: roundedRectangle
    // As per the regular rectangle
    property color color: "transparent"

    // As per regular rectangle
    property int radius: UM.Theme.getSize("default_radius").width

    // On what side should the corners be shown 5 can be used if no radius is needed.
    // 1 is down, 2 is left, 3 is up and 4 is right.
    property int cornerSide: RoundedRectangle.Direction.None

    // Simple object to ensure that border.width and border.color work
    property BorderGroup border: BorderGroup {}

    enum Direction
    {
        None = 0,
        Down = 1,
        Left = 2,
        Up = 3,
        Right = 4,
        All = 5
    }

    Rectangle
    {
        id: background
        anchors.fill: parent
        radius: cornerSide != RoundedRectangle.Direction.None ? parent.radius : 0
        color: parent.color
        border.width: parent.border.width
        border.color: parent.border.color
    }

    // The item that covers 2 of the corners to make them not rounded.
    Rectangle
    {
        visible: cornerSide != RoundedRectangle.Direction.None && cornerSide != RoundedRectangle.Direction.All
        height: cornerSide % 2 ? parent.radius: parent.height
        width: cornerSide % 2 ? parent.width : parent.radius
        color: parent.color
        anchors
        {
            right: cornerSide == RoundedRectangle.Direction.Left ? parent.right: undefined
            bottom: cornerSide == RoundedRectangle.Direction.Up ? parent.bottom: undefined
        }

        border.width: parent.border.width
        border.color: parent.border.color

        Rectangle
        {
            color: roundedRectangle.color
            height: cornerSide % 2 ? roundedRectangle.border.width: roundedRectangle.height - 2 * roundedRectangle.border.width
            width: cornerSide % 2 ? roundedRectangle.width - 2 * roundedRectangle.border.width: roundedRectangle.border.width
            anchors
            {
                right: cornerSide == RoundedRectangle.Direction.Right ? parent.right : undefined
                bottom: cornerSide  == RoundedRectangle.Direction.Down ? parent.bottom: undefined
                horizontalCenter: cornerSide % 2 ? parent.horizontalCenter: undefined
                verticalCenter: cornerSide % 2 ? undefined: parent.verticalCenter
            }
        }
    }
}
