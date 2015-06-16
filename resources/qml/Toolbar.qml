// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1

import UM 1.0 as UM

Item {
    id: base;

    width: buttons.width;
    height: buttons.height + panel.height;

    Rectangle {
        id: activeItemBackground;

        anchors.bottom: parent.bottom;

        width: UM.Theme.sizes.button.width;
        height: UM.Theme.sizes.button.height * 2;

        opacity: panelBackground.opacity;

        color: UM.Theme.colors.tool_panel_background

        function setActive(new_x) {
            x = new_x;
        }
    }

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

                checkable: true;
                checked: model.active;
                onCheckedChanged: if (checked) activeItemBackground.setActive(x);

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

    UM.AngledCornerRectangle {
        id: panelBackground;

        anchors.left: parent.left;
        anchors.bottom: buttons.top;
        anchors.bottomMargin: UM.Theme.sizes.default_margin.height;

        width: panel.item ? panel.width + 2 * UM.Theme.sizes.default_margin.width : 0;
        height: panel.item ? panel.height + 2 * UM.Theme.sizes.default_margin.height : 0;

        opacity: panel.item ? 1 : 0
        Behavior on opacity { NumberAnimation { duration: 100 } }

        color: UM.Theme.colors.tool_panel_background;
        cornerSize: width > 0 ? UM.Theme.sizes.default_margin.width : 0;

        Loader {
            id: panel

            x: UM.Theme.sizes.default_margin.width;
            y: UM.Theme.sizes.default_margin.height;

            source: UM.ActiveTool.valid ? UM.ActiveTool.activeToolPanel : "";
        }
    }
}
