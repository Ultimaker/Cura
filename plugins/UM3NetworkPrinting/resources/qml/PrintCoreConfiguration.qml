// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import UM 1.2 as UM

Item {
    id: extruderInfo;
    property var printCoreConfiguration: null;
    height: childrenRect.height;
    width: Math.round(parent.width / 2);

    // Extruder circle
    Item {
        id: extruderCircle;
        anchors.verticalCenter: parent.verticalCenter;
        height: UM.Theme.getSize("monitor_tab_extruder_circle").height;
        width: UM.Theme.getSize("monitor_tab_extruder_circle").width;

        // Loading skeleton
        Rectangle {
            anchors.fill: parent;
            color: UM.Theme.getColor("viewport_background");
            radius: Math.round(width / 2);
            visible: !printCoreConfiguration;
        }

        // Actual content
        Rectangle {
            anchors.fill: parent;
            border.width: UM.Theme.getSize("monitor_tab_thick_lining").width;
            border.color: UM.Theme.getColor("monitor_tab_lining_active");
            opacity: {
                if (printCoreConfiguration == null || printCoreConfiguration.activeMaterial == null || printCoreConfiguration.hotendID == null) {
                    return 0.5;
                }
                return 1;
            }
            radius: Math.round(width / 2);
            visible: printCoreConfiguration;

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
            right: parent.right;
            top: parent.top;
        }
        height: UM.Theme.getSize("monitor_tab_text_line").height;

        // Loading skeleton
        Rectangle {
            anchors.fill: parent;
            color: UM.Theme.getColor("viewport_background");
            visible: !extruderInfo.printCoreConfiguration;
        }

        // Actual content
        Label {
            anchors.fill: parent;
            elide: Text.ElideRight;
            font: UM.Theme.getFont("default");
            text: {
                if (printCoreConfiguration != undefined && printCoreConfiguration.activeMaterial != undefined) {
                    return printCoreConfiguration.activeMaterial.name;
                }
                return "";
            }
            visible: extruderInfo.printCoreConfiguration;
        }
    }

    Item {
        id: printCoreLabel;
        anchors {
            bottom: parent.bottom;
            left: extruderCircle.right;
            leftMargin: UM.Theme.getSize("default_margin").width;
            right: parent.right;
        }
        height: UM.Theme.getSize("monitor_tab_text_line").height;

        // Loading skeleton
        Rectangle {
            color: UM.Theme.getColor("viewport_background");
            height: parent.height;
            visible: !extruderInfo.printCoreConfiguration;
            width: parent.width / 3;
        }

        // Actual content
        Label {
            elide: Text.ElideRight;
            font: UM.Theme.getFont("default");
            opacity: 0.6;
            text: {
                if (printCoreConfiguration != undefined && printCoreConfiguration.hotendID != undefined) {
                    return printCoreConfiguration.hotendID;
                }
                return "";
            }
            visible: extruderInfo.printCoreConfiguration;
        }
    }
}
