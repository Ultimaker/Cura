// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.3
import QtQuick.Dialogs 1.1
import QtQuick.Controls 2.0
import QtQuick.Controls.Styles 1.3
import QtGraphicalEffects 1.0
import UM 1.3 as UM

Item {
    id: root;
    property var shadowRadius: UM.Theme.getSize("monitor_shadow_radius").width;
    property var shadowOffset: UM.Theme.getSize("monitor_shadow_offset").width;
    property var printer: null;
    property var collapsed: true;
    height: childrenRect.height + shadowRadius * 2; // Bubbles upward
    width: parent.width; // Bubbles downward

    // The actual card (white block)
    Rectangle {
        // 5px margin, but shifted 2px vertically because of the shadow
        anchors {
            bottomMargin: root.shadowRadius + root.shadowOffset;
            leftMargin: root.shadowRadius;
            rightMargin: root.shadowRadius;
            topMargin: root.shadowRadius - root.shadowOffset;
        }
        color: {
            if (!printer) {
                return UM.Theme.getColor("monitor_card_background_inactive");
            }
            if (printer.state == "disabled") {
                return UM.Theme.getColor("monitor_card_background_inactive");
            } else {
                return UM.Theme.getColor("monitor_card_background");
            }
        }
        height: childrenRect.height;
        layer.effect: DropShadow {
            radius: root.shadowRadius;
            verticalOffset: root.shadowOffset;
            color: "#3F000000"; // 25% shadow
        }
        layer.enabled: true
        width: parent.width - 2 * shadowRadius;

        Column {
            id: cardContents;
            height: childrenRect.height;
            width: parent.width;

            // Main card
            Item {
                id: mainCard;
                anchors {
                    left: parent.left;
                    leftMargin: UM.Theme.getSize("default_margin").width;
                    right: parent.right;
                    rightMargin: UM.Theme.getSize("default_margin").width;
                }
                height: 60 * screenScaleFactor + 2 * UM.Theme.getSize("default_margin").height;
                width: parent.width;

                // Machine icon
                Item {
                    id: machineIcon;
                    anchors.verticalCenter: parent.verticalCenter;
                    height: parent.height - 2 * UM.Theme.getSize("default_margin").width;
                    width: height;

                    // Skeleton
                    Rectangle {
                        anchors.fill: parent;
                        color: UM.Theme.getColor("monitor_skeleton_fill_dark");
                        radius: UM.Theme.getSize("default_margin").width;
                        visible: !printer;
                    }

                    // Content
                    UM.RecolorImage {
                        anchors.centerIn: parent;
                        color: {
                            if (printer && printer.activePrintJob != undefined) {
                                return UM.Theme.getColor("monitor_printer_icon");
                            }
                            return UM.Theme.getColor("monitor_printer_icon_inactive");
                        }
                        height: sourceSize.height;
                        source: {
                            if (!printer) {
                                return "";
                            }
                            switch(printer.type) {
                                case "Ultimaker 3":
                                    return "../svg/UM3-icon.svg";
                                case "Ultimaker 3 Extended":
                                    return "../svg/UM3x-icon.svg";
                                case "Ultimaker S5":
                                    return "../svg/UMs5-icon.svg";
                            }
                        }
                        visible: printer;
                        width: sourceSize.width;
                    }
                }

                // Printer info
                Item {
                    id: printerInfo;
                    anchors {
                        left: machineIcon.right;
                        leftMargin: UM.Theme.getSize("wide_margin").width;
                        right: collapseIcon.left;
                        verticalCenter: machineIcon.verticalCenter;
                    }
                    height: childrenRect.height;

                    // Machine name
                    Item {
                        id: machineNameLabel;
                        height: UM.Theme.getSize("monitor_text_line").height;
                        width: {
                            var percent = printer ? 0.75 : 0.3;
                            return Math.round(parent.width * percent);
                        }

                        // Skeleton
                        Rectangle {
                            anchors.fill: parent;
                            color: UM.Theme.getColor("monitor_skeleton_fill_dark");
                            visible: !printer;
                        }

                        // Actual content
                        Label {
                            anchors.fill: parent;
                            color: UM.Theme.getColor("text");
                            elide: Text.ElideRight;
                            font: UM.Theme.getFont("default_bold");
                            text: printer ? printer.name : "";
                            visible: printer;
                            width: parent.width;
                        }
                    }

                    // Job name
                    Item {
                        id: activeJobLabel;
                        anchors {
                            top: machineNameLabel.bottom;
                            topMargin: Math.round(UM.Theme.getSize("default_margin").height / 2);
                        }
                        height: UM.Theme.getSize("monitor_text_line").height;
                        width: Math.round(parent.width * 0.75);

                        // Skeleton
                        Rectangle {
                            anchors.fill: parent;
                            color: UM.Theme.getColor("monitor_skeleton_fill_dark");
                            visible: !printer;
                        }

                        // Actual content
                        Label {
                            anchors.fill: parent;
                            color: UM.Theme.getColor("monitor_text_inactive");
                            elide: Text.ElideRight;
                            font: UM.Theme.getFont("default");
                            text: {
                                if (!printer) {
                                    return "";
                                }
                                if (printer.state == "disabled") {
                                    return catalog.i18nc("@label", "Not available");
                                } else if (printer.state == "unreachable") {
                                    return catalog.i18nc("@label", "Unreachable");
                                }
                                if (printer.activePrintJob != null && printer.activePrintJob.name) {
                                    return printer.activePrintJob.name;
                                }
                                return catalog.i18nc("@label", "Available");
                            }
                            visible: printer;
                        }
                    }
                }

                // Collapse icon
                UM.RecolorImage {
                    id: collapseIcon;
                    anchors {
                        right: parent.right;
                        rightMargin: UM.Theme.getSize("default_margin").width;
                        verticalCenter: parent.verticalCenter;
                    }
                    color: UM.Theme.getColor("text");
                    height: 15 * screenScaleFactor; // TODO: Theme!
                    source: root.collapsed ? UM.Theme.getIcon("arrow_left") : UM.Theme.getIcon("arrow_bottom");
                    sourceSize {
                        height: height;
                        width: width;
                    }
                    visible: printer;
                    width: 15 * screenScaleFactor; // TODO: Theme!
                }

                MouseArea {
                    anchors.fill: parent;
                    enabled: printer;
                    onClicked: {
                        if (model && root.collapsed) {
                            printerList.currentIndex = model.index;
                        } else {
                            printerList.currentIndex = -1;
                        }
                    }
                }

                Connections {
                    target: printerList;
                    onCurrentIndexChanged: {
                        root.collapsed = printerList.currentIndex != model.index;
                    }
                }
            }
            // Detailed card
            PrinterCardDetails {
                collapsed: root.collapsed;
                printer: root.printer;
                visible: root.printer;
            }

            // Progress bar
            PrinterCardProgressBar {
                visible: printer && printer.activePrintJob != null;
                width: parent.width;
            }
        }
    }
}
