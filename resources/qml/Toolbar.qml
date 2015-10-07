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
    height: buttons.height
    property int activeY

    ColumnLayout {
        id: buttons;

        anchors.bottom: parent.bottom;
        anchors.left: parent.left;
        spacing: UM.Theme.sizes.default_lining.width

        Repeater {
            id: repeat

            model: UM.Models.toolModel

            Button {
                text: model.name
                iconSource: UM.Theme.icons[model.icon];

                checkable: true;
                checked: model.active;
                enabled: UM.Selection.hasSelection;

                style: UM.Theme.styles.tool_button;

                //Workaround since using ToolButton"s onClicked would break the binding of the checked property, instead
                //just catch the click so we do not trigger that behaviour.
                MouseArea {
                    anchors.fill: parent;
                    onClicked: {
                        parent.checked ? UM.Controller.setActiveTool(null) : UM.Controller.setActiveTool(model.id);
                        base.activeY = parent.y
                    }
                }
            }
        }
    }

    Rectangle {
        width: base.width
        height: base.height
        z: parent.z - 1
        anchors.verticalCenter: parent.verticalCenter
        anchors.horizontalCenter: parent.horizontalCenter
        color: UM.Theme.colors.lining
    }

    Rectangle {
        id: panelBackground;

        anchors.left: parent.right;
        y: base.activeY

        width: {
            if (panel.item && panel.width > 0){
                 return Math.max(panel.width + 2 * UM.Theme.sizes.default_margin.width)
            }
            else {
                return 0
            }
        }
        height: panel.item ? panel.height + 2 * UM.Theme.sizes.default_margin.height : 0;

        opacity: panel.item ? 1 : 0
        Behavior on opacity { NumberAnimation { duration: 100 } }

        color: UM.Theme.colors.tool_panel_background;
        border.width: UM.Theme.sizes.default_lining.width
        border.color: UM.Theme.colors.lining

        Loader {
            id: panel

            x: UM.Theme.sizes.default_margin.width;
            y: UM.Theme.sizes.default_margin.height;

            source: UM.ActiveTool.valid ? UM.ActiveTool.activeToolPanel : "";
        }
    }
}
