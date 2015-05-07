import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1

import UM 1.0 as UM

Item {
    id: base;

    width: buttons.width;
    height: buttons.height + panel.height;

    RowLayout {
        id: buttons;

        anchors.bottom: parent.bottom;
        anchors.left: parent.left;

        spacing: UM.Theme.sizes.default_margin.width * 2;

        Repeater {
            id: repeat

            model: UM.Models.toolModel

            Button {
                text: model.name;
                iconSource: UM.Theme.icons[model.icon];
                tooltip: model.description;

                checkable: true;
                checked: model.active;

                style: UM.Theme.styles.tool_button;

                //Workaround since using ToolButton"s onClicked would break the binding of the checked property, instead
                //just catch the click so we do not trigger that behaviour.
                MouseArea {
                    anchors.fill: parent;
                    onClicked: parent.checked ? UM.Controller.setActiveTool(null) : UM.Controller.setActiveTool(model.id);
                }
            }   
        }
    }

    Loader {
        id: panel

        anchors.left: parent.left;
        anchors.right: parent.right;
        anchors.bottom: buttons.top;
        anchors.bottomMargin: UM.Theme.sizes.default_margin.height;

        height: childrenRect.height;

        source: UM.ActiveTool.valid ? UM.ActiveTool.activeToolPanel : "";
    }
}
