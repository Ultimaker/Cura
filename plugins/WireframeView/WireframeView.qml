// Copyright (c) 2017 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.2
import QtQuick.Layouts 1.1
import QtQuick.Controls.Styles 1.1

import UM 1.0 as UM
import Cura 1.0 as Cura

Item
{
    width: {
        if (UM.LayerView.compatibilityMode) {
            return UM.Theme.getSize("wireframeview_menu_size_compatibility").width;
        } else {
            return UM.Theme.getSize("wireframeview_menu_size").width;
        }
    }
    height: {
        if (UM.LayerView.compatibilityMode) {
            return UM.Theme.getSize("wireframeview_menu_size_compatibility").height;
        } else {
            return UM.Theme.getSize("wireframeview_menu_size").height + UM.LayerView.extruderCount * (UM.Theme.getSize("wireframeview_row").height + UM.Theme.getSize("wireframeview_row_spacing").height)
        }
    }

    Rectangle {
        id: wireframeViewMenu
        anchors.left: parent.left
        anchors.top: parent.top
        width: parent.width
        height: parent.height
        color: UM.Theme.getColor("tool_panel_background")

        ColumnLayout {
            id: view_settings

            anchors.top: parent.top
            anchors.topMargin: UM.Theme.getSize("default_margin").height
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.getSize("default_margin").width
            spacing: UM.Theme.getSize("layerview_row_spacing").height

            Label
            {
                id: wireframeLabel
                anchors.left: parent.left
                text: catalog.i18nc("@label","View Mode: Wireframe")
                font.bold: true
                color: UM.Theme.getColor("text")
            }

            Label
            {
                anchors.left: parent.left
                text: " "
                font.pointSize: 0.5
            }

            Label
            {
                id: space2Label
                anchors.left: parent.left
                text: " "
                font.pointSize: 0.5
            }

            Repeater {
                model: ListModel {
                    id: typesLegendModel
                    Component.onCompleted:
                    {
                        typesLegendModel.append({
                            label: catalog.i18nc("@label", "Edges"),
                            colorId: "wireframeview_edge"
                        });
                        typesLegendModel.append({
                            label: catalog.i18nc("@label", "Overhang Edges"),
                            colorId: "wireframeview_overhang_edge"
                        });
                    }
                }

                Label {
                    text: label
                    Rectangle {
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.right: parent.right
                        width: UM.Theme.getSize("wireframeview_legend_size").width
                        height: UM.Theme.getSize("wireframeview_legend_size").height
                        color: UM.Theme.getColor(model.colorId)
                        border.width: UM.Theme.getSize("default_lining").width
                        border.color: UM.Theme.getColor("lining")
                    }
                    Layout.fillWidth: true
                    Layout.preferredHeight: UM.Theme.getSize("wireframeview_row").height + UM.Theme.getSize("default_lining").height
                    Layout.preferredWidth: UM.Theme.getSize("wireframeview_row").width
                }
            }
        }
    }
}
