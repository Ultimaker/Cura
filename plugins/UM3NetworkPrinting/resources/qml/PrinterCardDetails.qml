// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.3
import QtQuick.Dialogs 1.1
import QtQuick.Controls 2.0
import QtQuick.Controls.Styles 1.3
import QtGraphicalEffects 1.0
import QtQuick.Controls 1.4 as LegacyControls
import UM 1.3 as UM

Item {
    id: root;
    property var printer: null;
    property var printJob: printer ? printer.activePrintJob : null;
    property var collapsed: true;
    Behavior on height { NumberAnimation { duration: 100 } }
    Behavior on opacity { NumberAnimation { duration: 100 } }
    height: collapsed ? 0 : childrenRect.height;
    opacity: collapsed ? 0 : 1;
    width: parent.width;

    Column {
        id: contentColumn;
        anchors {
            left: parent.left;
            leftMargin: UM.Theme.getSize("default_margin").width;
            right: parent.right;
            rightMargin: UM.Theme.getSize("default_margin").width;
        }
        height: childrenRect.height + UM.Theme.getSize("default_margin").height;
        spacing: UM.Theme.getSize("default_margin").height;
        width: parent.width;

        HorizontalLine {}

        PrinterInfoBlock {
            printer: root.printer;
            printJob: root.printer ? root.printer.activePrintJob : null;
        }

        HorizontalLine {}

        Row {
            height: childrenRect.height;
            visible: root.printJob;
            width: parent.width;

            PrintJobTitle {
                job: root.printer ? root.printer.activePrintJob : null;
            }
            PrintJobContextMenu {
                id: contextButton;
                anchors {
                    right: parent.right;
                    rightMargin: UM.Theme.getSize("wide_margin").width;
                }
                printJob: root.printer ? root.printer.activePrintJob : null;
                visible: printJob;
            }
        }

        PrintJobPreview {
            anchors.horizontalCenter: parent.horizontalCenter;
            job: root.printer && root.printer.activePrintJob ? root.printer.activePrintJob : null;
            visible: root.printJob;
        }

        CameraButton {
            id: showCameraButton;
            iconSource: "../svg/camera-icon.svg";
            visible: root.printer;
        }
    }
}
