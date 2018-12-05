// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.3
import QtQuick.Dialogs 1.1
import QtQuick.Controls 2.0
import QtQuick.Controls.Styles 1.3
import QtGraphicalEffects 1.0
import QtQuick.Controls 1.4 as LegacyControls
import UM 1.3 as UM

// Includes printer type pill and extuder configurations

Item {
    id: root;
    property var printer: null;
    property var printJob: null;
    width: parent.width;
    height: childrenRect.height;

    // Printer family pills
    Row {
        id: printerFamilyPills;
        anchors {
            left: parent.left;
            right: parent.right;
        }
        height: childrenRect.height;
        spacing: Math.round(0.5 * UM.Theme.getSize("default_margin").width);
        width: parent.width;

        Repeater {
            id: compatiblePills;
            delegate: PrinterFamilyPill {
                text: modelData;
            }
            model: printJob ? printJob.compatibleMachineFamilies : [];
            visible: printJob;
            
        }

        PrinterFamilyPill {
            text: printer ? printer.type : "";
            visible: !compatiblePills.visible && printer;
        }
    }

    // Extruder info
    Row {
        id: extrudersInfo;
        anchors {
            left: parent.left;
            right: parent.right;
            rightMargin: UM.Theme.getSize("default_margin").width;
            top: printerFamilyPills.bottom;
            topMargin: UM.Theme.getSize("default_margin").height;
        }
        height: childrenRect.height;
        spacing: UM.Theme.getSize("default_margin").width;
        width: parent.width;

        PrintCoreConfiguration {
            width: Math.round(parent.width / 2) * screenScaleFactor;
            printCoreConfiguration: getExtruderConfig(0);
        }

        PrintCoreConfiguration {
            width: Math.round(parent.width / 2) * screenScaleFactor;
            printCoreConfiguration: getExtruderConfig(1);
        }
    }

    function getExtruderConfig( i ) {
        if (root.printJob) {
            // Use more-specific print job if possible
            return root.printJob.configuration.extruderConfigurations[i];
        }
        if (root.printer) {
            return root.printer.printerConfiguration.extruderConfigurations[i];
        }
        return null;
    }
}