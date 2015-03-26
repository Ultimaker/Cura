import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1

import UM 1.0 as UM

RowLayout {
    id: base;

    spacing: UM.Theme.sizes.default_margin.width * 2;

    Repeater {
        id: repeat

        model: UM.Models.toolModel

        PrinterButton {
            text: model.name;
            iconSource: UM.Theme.icons[model.icon];
            tooltip: model.description;

            checkable: true;
            checked: model.active;

            //Workaround since using ToolButton's onClicked would break the binding of the checked property, instead
            //just catch the click so we do not trigger that behaviour.
            MouseArea {
                anchors.fill: parent;
                onClicked: parent.checked ? UM.Controller.setActiveTool(null) : UM.Controller.setActiveTool(model.id);
            }
        }
    }
}
