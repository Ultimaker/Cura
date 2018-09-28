import QtQuick 2.3
import QtQuick.Dialogs 1.1
import QtQuick.Controls 2.0
import QtQuick.Controls.Styles 1.3
import QtGraphicalEffects 1.0
import QtQuick.Controls 1.4 as LegacyControls
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
            topMargin: root.shadowRadius - root.shadowOffset;
            bottomMargin: root.shadowRadius + root.shadowOffset;
            leftMargin: root.shadowRadius;
            rightMargin: root.shadowRadius;
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
            width: parent.width;
            height: childrenRect.height;

            // Main card
            Item {
                id: mainCard;
                // color: "pink";
                height: childrenRect.height;
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
                    height: 58;
                    width: 58;

                    // Skeleton
                    Rectangle {
                        anchors {
                            fill: parent;
                            // margins: Math.round(UM.Theme.getSize("default_margin").width / 4);
                        }
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
                                if (printer.state == "disabled") {
                                    return catalog.i18nc("@label", "Not available");
                                } else if (printer.state == "unreachable") {
                                    return catalog.i18nc("@label", "Unreachable");
                                }
                                if (printer.activePrintJob != null) {
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
                    height: 15; // TODO: Theme!
                    source: root.collapsed ? UM.Theme.getIcon("arrow_left") : UM.Theme.getIcon("arrow_bottom");
                    sourceSize.height: height;
                    sourceSize.width: width;
                    visible: printer;
                    width: 15; // TODO: Theme!
                }

                MouseArea {
                    anchors.fill: parent;
                    enabled: printer;
                    onClicked: {
                        console.log(model.index)
                        if (root.collapsed && model) {
                            printerList.currentIndex = model.index;
                        } else {
                            printerList.currentIndex = -1;
                        }
                    }
                }

                Connections {
                    target: printerList
                    onCurrentIndexChanged: {
                        root.collapsed = printerList.currentIndex != model.index;
                    }
                }
            }

            // Detailed card
            PrinterCardDetails {
                collapsed: root.collapsed;
                printer: printer;
                visible: printer;
            }

            // Progress bar
            PrinterCardProgressBar {
                visible: printer && printer.activePrintJob != null && printer.activePrintJob != undefined;
            }
        }
    }
}
