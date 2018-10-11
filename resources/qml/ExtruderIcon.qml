import QtQuick 2.7
import QtQuick.Controls 1.1
import UM 1.2 as UM

Item
{

    id: extruderIconItem

    implicitWidth: UM.Theme.getSize("button").width
    implicitHeight: implicitWidth

    property bool checked: true
    property alias material_color: materialColorCircle.color
    property alias text_color: extruderNumberText.color

    UM.RecolorImage
    {
        id: mainCircle
        anchors.fill: parent

        sourceSize.width: parent.width
        sourceSize.height: parent.width
        source: UM.Theme.getIcon("extruder_button")
        color: extruderNumberText.color
    }

    Label
    {
        id: extruderNumberText
        anchors.centerIn: parent
        text: index + 1;
        font: UM.Theme.getFont("default_bold")
    }

    // Material colour circle
    // Only draw the filling colour of the material inside the SVG border.
    Rectangle
    {
        id: materialColorCircle

        anchors
        {
            right: parent.right
        }

        width: Math.round(parent.width * 0.35)
        height: Math.round(parent.height * 0.35)
        radius: Math.round(width / 2)

        border.width: 1
        border.color: UM.Theme.getColor("extruder_button_material_border")

        opacity: !extruderIconItem.checked ? 0.6 : 1.0
    }
}