// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import UM 1.3 as UM
import Cura 1.0 as Cura

Component {
    Rectangle {
        id: monitorFrame;
        property var emphasisColor: UM.Theme.getColor("setting_control_border_highlight");
        property var cornerRadius: UM.Theme.getSize("monitor_corner_radius").width;
        color: UM.Theme.getColor("viewport_background");
        height: maximumHeight;
        onVisibleChanged: {
            if (monitorFrame != null && !monitorFrame.visible) {
                OutputDevice.setActiveCameraUrl("");
            }
        }
        width: maximumWidth;

        UM.I18nCatalog {
            id: catalog;
            name: "cura";
        }

        Label {
            id: manageQueueLabel;
            anchors {
                bottom: queuedLabel.bottom;
                right: queuedPrintJobs.right;
                rightMargin: 3 * UM.Theme.getSize("default_margin").width;
            }
            color: UM.Theme.getColor("primary");
            font: UM.Theme.getFont("default");
            linkColor: UM.Theme.getColor("primary");
            text: catalog.i18nc("@label link to connect manager", "Manage queue");
        }

        MouseArea {
            anchors.fill: manageQueueLabel;
            hoverEnabled: true;
            onClicked: Cura.MachineManager.printerOutputDevices[0].openPrintJobControlPanel();
            onEntered: manageQueueLabel.font.underline = true;
            onExited: manageQueueLabel.font.underline = false;
        }

        Label {
            id: queuedLabel;
            anchors {
                left: queuedPrintJobs.left;
                leftMargin: 3 * UM.Theme.getSize("default_margin").width + 5 * screenScaleFactor;
                top: parent.top;
                topMargin: 2 * UM.Theme.getSize("default_margin").height;
            }
            color: UM.Theme.getColor("text");
            font: UM.Theme.getFont("large");
            text: catalog.i18nc("@label", "Queued");
        }

        Column {
            id: skeletonLoader;
            anchors {
                bottom: parent.bottom;
                bottomMargin: UM.Theme.getSize("default_margin").height;
                horizontalCenter: parent.horizontalCenter;
                top: queuedLabel.bottom;
                topMargin: UM.Theme.getSize("default_margin").height;
            }
            visible: !queuedPrintJobs.visible;
            width: Math.min(800 * screenScaleFactor, maximumWidth);

            PrintJobInfoBlock {
                anchors {
                    left: parent.left;
                    leftMargin: UM.Theme.getSize("default_margin").width;
                    right: parent.right;
                    rightMargin: UM.Theme.getSize("default_margin").width;
                }
                printJob: null; // Use as skeleton
            }

            PrintJobInfoBlock {
                anchors {
                    left: parent.left;
                    leftMargin: UM.Theme.getSize("default_margin").width;
                    right: parent.right;
                    rightMargin: UM.Theme.getSize("default_margin").width;
                }
                printJob: null; // Use as skeleton
            }
        }

        ScrollView {
            id: queuedPrintJobs;
            anchors {
                top: queuedLabel.bottom;
                topMargin: UM.Theme.getSize("default_margin").height;
                horizontalCenter: parent.horizontalCenter;
                bottomMargin: UM.Theme.getSize("default_margin").height;
                bottom: parent.bottom;
            }
            style: UM.Theme.styles.scrollview;
            visible: OutputDevice.receivedPrintJobs;
            width: Math.min(800 * screenScaleFactor, maximumWidth);

            ListView {
                id: printJobList;
                anchors.fill: parent;
                delegate: PrintJobInfoBlock {
                    anchors {
                        left: parent.left;
                        leftMargin: UM.Theme.getSize("default_margin").width;
                        right: parent.right;
                        rightMargin: UM.Theme.getSize("default_margin").width;
                    }
                    printJob: modelData;
                }
                model: OutputDevice.queuedPrintJobs;
                spacing: UM.Theme.getSize("default_margin").height - 2 * UM.Theme.getSize("monitor_shadow_radius").width;
            }
        }

        PrinterVideoStream {
            anchors.fill: parent;
            cameraUrl: OutputDevice.activeCameraUrl;
            visible: OutputDevice.activeCameraUrl != "";
        }
    }
}
