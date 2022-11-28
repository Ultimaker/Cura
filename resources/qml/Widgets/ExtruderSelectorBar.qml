import QtQuick 2.12
import QtQuick.Controls 2.12
import QtQuick.Layouts 1.3

import UM 1.5 as UM
import Cura 1.5 as Cura

Row
{
    id: extruderSelectionBar
    property alias model: extruderButtonRepeater.model

    spacing: 0
    width: parent.width
    height: childrenRect.height

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
                isTopElement: extrudersModel.getItem(0).id == model.id
                isBottomElement: extrudersModel.getItem(extrudersModel.rowCount() - 1).id == model.id
                iconScale: 0.6
                buttonSize: UM.Theme.getSize("large_button").width
            }
        }
    }
}
