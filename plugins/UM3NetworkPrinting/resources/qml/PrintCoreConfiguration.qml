// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import UM 1.2 as UM

Item {
    id: extruderInfo

    property var printCoreConfiguration: null;

    width: Math.round(parent.width / 2);
    height: childrenRect.height;

    // Extruder circle
    Item {
        id: extruderCircle

        width: UM.Theme.getSize("monitor_tab_extruder_circle").width;
        height: UM.Theme.getSize("monitor_tab_extruder_circle").height;
        anchors.verticalCenter: parent.verticalCenter;

        // Loading skeleton
        Rectangle {
            visible: !printCoreConfiguration;
            anchors.fill: parent;
            radius: Math.round(width / 2);
            color: UM.Theme.getColor("viewport_background");
        }

        // Actual content
        Rectangle {
            visible: printCoreConfiguration;
            anchors.fill: parent;
            radius: Math.round(width / 2);
            border.width: UM.Theme.getSize("monitor_tab_thick_lining").width;
            border.color: UM.Theme.getColor("monitor_tab_lining_active");
            opacity: {
                if (printCoreConfiguration == null || printCoreConfiguration.activeMaterial == null || printCoreConfiguration.hotendID == null) {
                    return 0.5;
                }
                return 1;
            }

            Label {
                anchors.centerIn: parent;
                font: UM.Theme.getFont("default_bold");
                text: printCoreConfiguration ? printCoreConfiguration.position + 1 : 0;
            }
        }
    }

    // Print core and material labels
    Item {
        id: materialLabel

        anchors {
            left: extruderCircle.right;
            leftMargin: UM.Theme.getSize("default_margin").width;
            top: parent.top;
            right: parent.right;
        }
        height: UM.Theme.getSize("monitor_tab_text_line").height;

        // Loading skeleton
        Rectangle {
            visible: !extruderInfo.printCoreConfiguration;
            anchors.fill: parent;
            color: UM.Theme.getColor("viewport_background");
        }

        // Actual content
        Label {
            visible: extruderInfo.printCoreConfiguration;
            anchors.fill: parent;
            text: {
                if (printCoreConfiguration != undefined && printCoreConfiguration.activeMaterial != undefined) {
                    return printCoreConfiguration.activeMaterial.name;
                }
                return "";
            }
            font: UM.Theme.getFont("default");
            elide: Text.ElideRight;
        }
    }

    Item {
        id: printCoreLabel;

        anchors {
            right: parent.right;
            left: extruderCircle.right;
            leftMargin: UM.Theme.getSize("default_margin").width;
            bottom: parent.bottom;
        }
        height: UM.Theme.getSize("monitor_tab_text_line").height;

        // Loading skeleton
        Rectangle {
            visible: !extruderInfo.printCoreConfiguration;
            width: parent.width / 3;
            height: parent.height;
            color: UM.Theme.getColor("viewport_background");
        }

        // Actual content
        Label {
            visible: extruderInfo.printCoreConfiguration;
            text: {
                if (printCoreConfiguration != undefined && printCoreConfiguration.hotendID != undefined) {
                    return printCoreConfiguration.hotendID;
                }
                return "";
            }
            elide: Text.ElideRight;
            opacity: 0.6;
            font: UM.Theme.getFont("default");
        }
    }
}
