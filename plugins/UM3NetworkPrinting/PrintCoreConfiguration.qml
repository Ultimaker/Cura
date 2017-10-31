import QtQuick 2.2
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4

import UM 1.2 as UM


Item
{
    id: extruderInfo
    property var printCoreConfiguration

    width: Math.floor(parent.width / 2)
    height: childrenRect.height
    Label
    {
        id: materialLabel
        text: printCoreConfiguration.material.material + " (" + printCoreConfiguration.material.color + ")"
        elide: Text.ElideRight
        width: parent.width
        font: UM.Theme.getFont("very_small")
    }
    Label
    {
        id: printCoreLabel
        text: printCoreConfiguration.print_core_id
        anchors.top: materialLabel.bottom
        elide: Text.ElideRight
        width: parent.width
        font: UM.Theme.getFont("very_small")
        opacity: 0.5
    }
}
