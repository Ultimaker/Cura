// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.3
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.3
import UM 1.3 as UM
import Cura 1.0 as Cura

Component {
    Rectangle {
        id: base;
        property var shadowRadius: UM.Theme.getSize("monitor_shadow_radius").width;
        property var cornerRadius: UM.Theme.getSize("monitor_corner_radius").width;
        anchors.fill: parent;
        color: UM.Theme.getColor("sidebar");
        visible: OutputDevice != null;

        UM.I18nCatalog {
            id: catalog;
            name: "cura";
        }

        Label {
            id: printingLabel;
            anchors {
                left: parent.left;
                leftMargin: 4 * UM.Theme.getSize("default_margin").width;
                margins: 2 * UM.Theme.getSize("default_margin").width;
                right: parent.right;
                top: parent.top;
            }
            color: UM.Theme.getColor("text");
            elide: Text.ElideRight;
            font: UM.Theme.getFont("large");
            text: catalog.i18nc("@label", "Printing");
        }

        Label {
            id: managePrintersLabel;
            anchors {
                bottom: printingLabel.bottom;
                right: printerScrollView.right;
                rightMargin: 4 * UM.Theme.getSize("default_margin").width;
            }
            color: UM.Theme.getColor("primary"); // "Cura Blue"
            font: UM.Theme.getFont("default");
            linkColor: UM.Theme.getColor("primary"); // "Cura Blue"
            text: catalog.i18nc("@label link to connect manager", "Manage printers");
        }

        MouseArea {
            anchors.fill: managePrintersLabel;
            hoverEnabled: true;
            onClicked: Cura.MachineManager.printerOutputDevices[0].openPrinterControlPanel();
            onEntered: managePrintersLabel.font.underline = true;
            onExited: managePrintersLabel.font.underline = false;
        }

        // Skeleton loading
        Column {
            id: skeletonLoader;
            anchors {
                left: parent.left;
                leftMargin: UM.Theme.getSize("wide_margin").width;
                right: parent.right;
                rightMargin: UM.Theme.getSize("wide_margin").width;
                top: printingLabel.bottom;
                topMargin: UM.Theme.getSize("default_margin").height;
            }
            spacing: UM.Theme.getSize("default_margin").height - 10;
            visible: printerList.count === 0;

            PrinterCard {
                printer: null;
            }
            PrinterCard {
                printer: null;
            }
        }

        // Actual content
        ScrollView {
            id: printerScrollView;
            anchors {
                bottom: parent.bottom;
                left: parent.left;
                right: parent.right;
                top: printingLabel.bottom;
                topMargin: UM.Theme.getSize("default_margin").height;
            }
            style: UM.Theme.styles.scrollview;

            ListView {
                id: printerList;
                property var currentIndex: -1;
                anchors {
                    fill: parent;
                    leftMargin: UM.Theme.getSize("wide_margin").width;
                    rightMargin: UM.Theme.getSize("wide_margin").width;
                }
                delegate: PrinterCard {
                    printer: modelData;
                }
                model: OutputDevice.printers;
                spacing: UM.Theme.getSize("default_margin").height - 10;
            }
        }
    }
}
