import QtQuick 2.12
import QtQuick.Controls 2.12
import QtQuick.Layouts 1.3

import UM 1.5 as UM
import Cura 1.5 as Cura

Row
{
    id: extruderSelectionBar

    width: parent.width
    height: childrenRect.height
    spacing: 0

    property alias model: extruderButtonRepeater.model
    property int selectedIndex: 0
    function onClickExtruder(index) {}


    Repeater
    {
        id: extruderButtonRepeater

        delegate: Item
        {
            width: {
                const maximum_width = Math.floor(extruderSelectionBar.width / extruderButtonRepeater.count);
                return Math.min(UM.Theme.getSize("large_button").width, maximum_width);
            }
            height: childrenRect.height

            Cura.ExtruderButton
            {
                extruder: model
                checked: extruder.index == selectedIndex
                iconScale: 0.6
                buttonSize: UM.Theme.getSize("large_button").width
                onClicked: extruder.enabled && onClickExtruder(extruder.index)
            }
        }
    }
}
