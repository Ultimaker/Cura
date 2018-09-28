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

        // Main card
        Rectangle {
            id: mainCard;
            anchors.top: parent.top;
            color: "pink";
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
                    console.log(printerInfo.height)
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
        Rectangle {
            width: parent.width;
            height: 0;
            anchors.top: mainCard.bottom;
            anchors.bottom: progressBar.top;
        }

        // Progress bar
        PrinterCardProgressBar {
            id: progressBar;
            anchors {
                bottom: parent.bottom;
            }
            visible: printer && printer.activePrintJob != null && printer.activePrintJob != undefined;
            width: parent.width;
        }
    }
}

















    //     Item
    //     {
    //         id: detailedInfo
    //         property var printJob: printer.activePrintJob
    //         visible: height == childrenRect.height
    //         anchors.top: printerInfo.bottom
    //         width: parent.width
    //         height: !root.collapsed ? childrenRect.height : 0
    //         opacity: visible ? 1 : 0
    //         Behavior on height { NumberAnimation { duration: 100 } }
    //         Behavior on opacity { NumberAnimation { duration: 100 } }
    //         Rectangle
    //         {
    //             id: topSpacer
    //             color:
    //             {
    //                 if(printer.state == "disabled")
    //                 {
    //                     return UM.Theme.getColor("monitor_lining_inactive")
    //                 }
    //                 return UM.Theme.getColor("viewport_background")
    //             }
    //             // UM.Theme.getColor("viewport_background")
    //             height: 1
    //             anchors
    //             {
    //                 left: parent.left
    //                 right: parent.right
    //                 margins: UM.Theme.getSize("default_margin").width
    //                 top: parent.top
    //                 topMargin: UM.Theme.getSize("default_margin").width
    //             }
    //         }
    //         PrinterFamilyPill
    //         {
    //             id: printerFamilyPill
    //             color:
    //             {
    //                 if(printer.state == "disabled")
    //                 {
    //                     return "transparent"
    //                 }
    //                 return UM.Theme.getColor("viewport_background")
    //             }
    //             anchors.top: topSpacer.bottom
    //             anchors.topMargin: 2 * UM.Theme.getSize("default_margin").height
    //             text: printer.type
    //             anchors.left: parent.left
    //             anchors.leftMargin: UM.Theme.getSize("default_margin").width
    //             padding: 3
    //         }
    //         Row
    //         {
    //             id: extrudersInfo
    //             anchors.top: printerFamilyPill.bottom
    //             anchors.topMargin: 2 * UM.Theme.getSize("default_margin").height
    //             anchors.left: parent.left
    //             anchors.leftMargin: 2 * UM.Theme.getSize("default_margin").width
    //             anchors.right: parent.right
    //             anchors.rightMargin: 2 * UM.Theme.getSize("default_margin").width
    //             height: childrenRect.height
    //             spacing: UM.Theme.getSize("default_margin").width

    //             PrintCoreConfiguration
    //             {
    //                 id: leftExtruderInfo
    //                 width: Math.round(parent.width  / 2)
    //                 printCoreConfiguration: printer.printerConfiguration.extruderConfigurations[0]
    //             }

    //             PrintCoreConfiguration
    //             {
    //                 id: rightExtruderInfo
    //                 width: Math.round(parent.width / 2)
    //                 printCoreConfiguration: printer.printerConfiguration.extruderConfigurations[1]
    //             }
    //         }

    //         Rectangle
    //         {
    //             id: jobSpacer
    //             color: UM.Theme.getColor("viewport_background")
    //             height: 2
    //             anchors
    //             {
    //                 left: parent.left
    //                 right: parent.right
    //                 margins: UM.Theme.getSize("default_margin").width
    //                 top: extrudersInfo.bottom
    //                 topMargin: 2 * UM.Theme.getSize("default_margin").height
    //             }
    //         }

    //         Item
    //         {
    //             id: jobInfo
    //             property var showJobInfo: printer.activePrintJob != null && printer.activePrintJob.state != "queued"

    //             anchors.top: jobSpacer.bottom
    //             anchors.topMargin: 2 * UM.Theme.getSize("default_margin").height
    //             anchors.left: parent.left
    //             anchors.right: parent.right
    //             anchors.margins: UM.Theme.getSize("default_margin").width
    //             anchors.leftMargin: 2 * UM.Theme.getSize("default_margin").width
    //             height: showJobInfo ? childrenRect.height + 2 * UM.Theme.getSize("default_margin").height: 0
    //             visible: showJobInfo
    //             Label
    //             {
    //                 id: printJobName
    //                 text: printer.activePrintJob != null ? printer.activePrintJob.name : ""
    //                 font: UM.Theme.getFont("default_bold")
    //                 anchors.left: parent.left
    //                 anchors.right: contextButton.left
    //                 anchors.rightMargin: UM.Theme.getSize("default_margin").width
    //                 elide: Text.ElideRight
    //             }
    //             Label
    //             {
    //                 id: ownerName
    //                 anchors.top: printJobName.bottom
    //                 text: printer.activePrintJob != null ? printer.activePrintJob.owner : ""
    //                 font: UM.Theme.getFont("default")
    //                 opacity: 0.6
    //                 width: parent.width
    //                 elide: Text.ElideRight
    //             }

    //             function switchPopupState()
    //             {
    //                 popup.visible ? popup.close() : popup.open()
    //             }

    //             Button
    //             {
    //                 id: contextButton
    //                 text: "\u22EE" //Unicode; Three stacked points.
    //                 width: 35
    //                 height: width
    //                 anchors
    //                 {
    //                     right: parent.right
    //                     top: parent.top
    //                 }
    //                 hoverEnabled: true

    //                 background: Rectangle
    //                 {
    //                     opacity: contextButton.down || contextButton.hovered ? 1 : 0
    //                     width: contextButton.width
    //                     height: contextButton.height
    //                     radius: 0.5 * width
    //                     color: UM.Theme.getColor("viewport_background")
    //                 }
    //                 contentItem: Label
    //                 {
    //                     text: contextButton.text
    //                     color: UM.Theme.getColor("monitor_tab_text_inactive")
    //                     font.pixelSize: 25
    //                     verticalAlignment: Text.AlignVCenter
    //                     horizontalAlignment: Text.AlignHCenter
    //                 }

    //                 onClicked: parent.switchPopupState()
    //             }

    //             Popup
    //             {
    //                 // TODO Change once updating to Qt5.10 - The 'opened' property is in 5.10 but the behavior is now implemented with the visible property
    //                 id: popup
    //                 clip: true
    //                 closePolicy: Popup.CloseOnPressOutside
    //                 x: (parent.width - width) + 26 * screenScaleFactor
    //                 y: contextButton.height - 5 * screenScaleFactor // Because shadow
    //                 width: 182 * screenScaleFactor
    //                 height: contentItem.height + 2 * padding
    //                 visible: false
    //                 padding: 5 * screenScaleFactor // Because shadow

    //                 transformOrigin: Popup.Top
    //                 contentItem: Item
    //                 {
    //                     width: popup.width
    //                     height: childrenRect.height + 36 * screenScaleFactor
    //                     anchors.topMargin: 10 * screenScaleFactor
    //                     anchors.bottomMargin: 10 * screenScaleFactor
    //                     Button
    //                     {
    //                         id: pauseButton
    //                         text: printer.activePrintJob != null && printer.activePrintJob.state == "paused" ? catalog.i18nc("@label", "Resume") : catalog.i18nc("@label", "Pause")
    //                         onClicked:
    //                         {
    //                             if(printer.activePrintJob.state == "paused")
    //                             {
    //                                 printer.activePrintJob.setState("print")
    //                             }
    //                             else if(printer.activePrintJob.state == "printing")
    //                             {
    //                                 printer.activePrintJob.setState("pause")
    //                             }
    //                             popup.close()
    //                         }
    //                         width: parent.width
    //                         enabled: printer.activePrintJob != null && ["paused", "printing"].indexOf(printer.activePrintJob.state) >= 0
    //                         visible: enabled
    //                         anchors.top: parent.top
    //                         anchors.topMargin: 18 * screenScaleFactor
    //                         height: visible ? 39 * screenScaleFactor : 0 * screenScaleFactor
    //                         hoverEnabled: true
    //                         background: Rectangle
    //                         {
    //                             opacity: pauseButton.down || pauseButton.hovered ? 1 : 0
    //                             color: UM.Theme.getColor("viewport_background")
    //                         }
    //                         contentItem: Label
    //                         {
    //                             text: pauseButton.text
    //                             horizontalAlignment: Text.AlignLeft
    //                             verticalAlignment: Text.AlignVCenter
    //                         }
    //                     }

    //                     Button
    //                     {
    //                         id: abortButton
    //                         text: catalog.i18nc("@label", "Abort")
    //                         onClicked:
    //                         {
    //                             abortConfirmationDialog.visible = true;
    //                             popup.close();
    //                         }
    //                         width: parent.width
    //                         height: 39 * screenScaleFactor
    //                         anchors.top: pauseButton.bottom
    //                         hoverEnabled: true
    //                         enabled: printer.activePrintJob != null && ["paused", "printing", "pre_print"].indexOf(printer.activePrintJob.state) >= 0
    //                         background: Rectangle
    //                         {
    //                             opacity: abortButton.down || abortButton.hovered ? 1 : 0
    //                             color: UM.Theme.getColor("viewport_background")
    //                         }
    //                         contentItem: Label
    //                         {
    //                             text: abortButton.text
    //                             horizontalAlignment: Text.AlignLeft
    //                             verticalAlignment: Text.AlignVCenter
    //                         }
    //                     }

    //                     MessageDialog
    //                     {
    //                         id: abortConfirmationDialog
    //                         title: catalog.i18nc("@window:title", "Abort print")
    //                         icon: StandardIcon.Warning
    //                         text: catalog.i18nc("@label %1 is the name of a print job.", "Are you sure you want to abort %1?").arg(printer.activePrintJob.name)
    //                         standardButtons: StandardButton.Yes | StandardButton.No
    //                         Component.onCompleted: visible = false
    //                         onYes: printer.activePrintJob.setState("abort")
    //                     }
    //                 }

    //                 background: Item
    //                 {
    //                     width: popup.width
    //                     height: popup.height

    //                     DropShadow
    //                     {
    //                         anchors.fill: pointedRectangle
    //                         radius: 5
    //                         color: "#3F000000"  // 25% shadow
    //                         source: pointedRectangle
    //                         transparentBorder: true
    //                         verticalOffset: 2
    //                     }

    //                     Item
    //                     {
    //                         id: pointedRectangle
    //                         width: parent.width - 10 * screenScaleFactor // Because of the shadow
    //                         height: parent.height - 10 * screenScaleFactor // Because of the shadow
    //                         anchors.horizontalCenter: parent.horizontalCenter
    //                         anchors.verticalCenter: parent.verticalCenter

    //                         Rectangle
    //                         {
    //                             id: point
    //                             height: 14 * screenScaleFactor
    //                             width: 14 * screenScaleFactor
    //                             color: UM.Theme.getColor("setting_control")
    //                             transform: Rotation { angle: 45}
    //                             anchors.right: bloop.right
    //                             anchors.rightMargin: 24
    //                             y: 1
    //                         }

    //                         Rectangle
    //                         {
    //                             id: bloop
    //                             color: UM.Theme.getColor("setting_control")
    //                             width: parent.width
    //                             anchors.top: parent.top
    //                             anchors.topMargin: 8 * screenScaleFactor // Because of the shadow + point
    //                             anchors.bottom: parent.bottom
    //                             anchors.bottomMargin: 8 * screenScaleFactor // Because of the shadow
    //                         }
    //                     }
    //                 }

    //                 exit: Transition
    //                 {
    //                     // This applies a default NumberAnimation to any changes a state change makes to x or y properties
    //                     NumberAnimation { property: "visible"; duration: 75; }
    //                 }
    //                 enter: Transition
    //                 {
    //                     // This applies a default NumberAnimation to any changes a state change makes to x or y properties
    //                     NumberAnimation { property: "visible"; duration: 75; }
    //                 }

    //                 onClosed: visible = false
    //                 onOpened: visible = true
    //             }

    //             Image
    //             {
    //                 id: printJobPreview
    //                 source: printer.activePrintJob != null ? printer.activePrintJob.previewImageUrl : ""
    //                 anchors.top: ownerName.bottom
    //                 anchors.horizontalCenter: parent.horizontalCenter
    //                 width: parent.width / 2
    //                 height: width
    //                 opacity:
    //                 {
    //                     if(printer.activePrintJob == null)
    //                     {
    //                         return 1.0
    //                     }

    //                     switch(printer.activePrintJob.state)
    //                     {
    //                         case "wait_cleanup":
    //                         case "wait_user_action":
    //                         case "paused":
    //                             return 0.5
    //                         default:
    //                             return 1.0
    //                     }
    //                 }


    //             }

    //             UM.RecolorImage
    //             {
    //                 id: statusImage
    //                 anchors.centerIn: printJobPreview
    //                 source:
    //                 {
    //                     if(printer.activePrintJob == null)
    //                     {
    //                         return ""
    //                     }
    //                     switch(printer.activePrintJob.state)
    //                     {
    //                         case "paused":
    //                             return "../svg/paused-icon.svg"
    //                         case "wait_cleanup":
    //                             if(printer.activePrintJob.timeElapsed < printer.activePrintJob.timeTotal)
    //                             {
    //                                 return "../svg/aborted-icon.svg"
    //                             }
    //                             return "../svg/approved-icon.svg"
    //                         case "wait_user_action":
    //                             return "../svg/aborted-icon.svg"
    //                         default:
    //                             return ""
    //                     }
    //                 }
    //                 visible: source != ""
    //                 width: 0.5 * printJobPreview.width
    //                 height: 0.5 * printJobPreview.height
    //                 sourceSize.width: width
    //                 sourceSize.height: height
    //                 color: "black"
    //             }

    //             CameraButton
    //             {
    //                 id: showCameraButton
    //                 iconSource: "../svg/camera-icon.svg"
    //                 anchors
    //                 {
    //                     left: parent.left
    //                     bottom: printJobPreview.bottom
    //                 }
    //             }
    //         }
    //     }
    // }