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
    property var shadowRadius: 5;
    property var shadowOffset: 2;
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
            if (printer.state == "disabled") {
                return UM.Theme.getColor("monitor_tab_background_inactive");
            } else {
                return UM.Theme.getColor("monitor_tab_background_active");
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
            height: childrenRect.height;
            width: parent.width;

            // Main card
            Item {
                id: mainCard;
                // I don't know why the extra height is needed but it is in order to look proportional.
                height: childrenRect.height + 2;
                width: parent.width;

                // Machine icon
                Item {
                    id: machineIcon;
                    anchors {
                        left: parent.left;
                        leftMargin: UM.Theme.getSize("wide_margin").width;
                        margins: UM.Theme.getSize("default_margin").width;
                        top: parent.top;
                    }
                    height: 58 * screenScaleFactor;
                    width: 58 * screenScaleFactor;

                    // Skeleton
                    Rectangle {
                        anchors.fill: parent;
                        color: UM.Theme.getColor("viewport_background"); // TODO: Theme!
                        radius: UM.Theme.getSize("default_margin").width; // TODO: Theme!
                        visible: !printer;
                    }

                    // Content
                    UM.RecolorImage {
                        anchors.centerIn: parent;
                        color: {
                            if (printer.state == "disabled") {
                                return UM.Theme.getColor("monitor_tab_text_inactive");
                            }
                            if (printer.activePrintJob != undefined) {
                                return UM.Theme.getColor("primary");
                            }
                            return UM.Theme.getColor("monitor_tab_text_inactive");
                        }
                        height: sourceSize.height;
                        source: {
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
                    height: childrenRect.height
                    anchors {
                        left: machineIcon.right;
                        leftMargin: UM.Theme.getSize("default_margin").width;
                        right: collapseIcon.left;
                        rightMargin: UM.Theme.getSize("default_margin").width;
                        verticalCenter: machineIcon.verticalCenter;
                    }

                    // Machine name
                    Item {
                        id: machineNameLabel;
                        height: UM.Theme.getSize("monitor_tab_text_line").height;
                        width: parent.width * 0.3;

                        // Skeleton
                        Rectangle {
                            anchors.fill: parent;
                            color: UM.Theme.getColor("viewport_background"); // TODO: Theme!
                            visible: !printer;
                        }

                        // Actual content
                        Label {
                            anchors.fill: parent;
                            elide: Text.ElideRight;
                            font: UM.Theme.getFont("default_bold");
                            text: printer.name;
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
                        height: UM.Theme.getSize("monitor_tab_text_line").height;
                        width: parent.width * 0.75;

                        // Skeleton
                        Rectangle {
                            anchors.fill: parent;
                            color: UM.Theme.getColor("viewport_background"); // TODO: Theme!
                            visible: !printer;
                        }

                        // Actual content
                        Label {
                            anchors.fill: parent;
                            color: UM.Theme.getColor("monitor_tab_text_inactive");
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
                        if (!model) {
                            return;
                        }
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
                visible: printer && printer.activePrintJob != null && printer.activePrintJob != undefined;
            }
        }
    }
}
