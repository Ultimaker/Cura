// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Dialogs 1.1
import QtQuick.Controls 2.0
import QtQuick.Controls.Styles 1.4
import QtGraphicalEffects 1.0
import QtQuick.Layouts 1.1
import QtQuick.Dialogs 1.1
import UM 1.3 as UM

Item {
    id: root

    property var shadowRadius: 5;
    property var shadowOffset: 2;
    property var debug: false;
    property var printJob: null;

    width: parent.width; // Bubbles downward
    height: childrenRect.height + shadowRadius * 2; // Bubbles upward

    UM.I18nCatalog {
        id: catalog;
        name: "cura";
    }

    // The actual card (white block)
    Rectangle {
        color: "white"; // TODO: Theme!
        height: childrenRect.height;
        width: parent.width - shadowRadius * 2;

        // 5px margin, but shifted 2px vertically because of the shadow
        anchors {
            topMargin: root.shadowRadius - root.shadowOffset;
            bottomMargin: root.shadowRadius + root.shadowOffset;
            leftMargin: root.shadowRadius;
            rightMargin: root.shadowRadius;
        }
        layer.enabled: true
        layer.effect: DropShadow {
            radius: root.shadowRadius
            verticalOffset: 2 * screenScaleFactor
            color: "#3F000000" // 25% shadow
        }

        Column {
            width: parent.width;
            height: childrenRect.height;

            // Main content
            Item {
                id: mainContent;
                width: parent.width;
                height: 200; // TODO: Theme!

                // Left content
                Item {
                    anchors {
                        left: parent.left;
                        right: parent.horizontalCenter;
                        top: parent.top;
                        bottom: parent.bottom;
                        margins: UM.Theme.getSize("wide_margin").width
                    }

                    Item {
                        id: printJobName;

                        width: parent.width;
                        height: UM.Theme.getSize("monitor_tab_text_line").height;

                        Rectangle {
                            visible: !printJob;
                            color: UM.Theme.getColor("viewport_background"); // TODO: Theme!
                            height: parent.height;
                            width: parent.width / 3;
                        }
                        Label {
                            visible: printJob;
                            text: printJob ? printJob.name : ""; // Supress QML warnings
                            font: UM.Theme.getFont("default_bold");
                            elide: Text.ElideRight;
                            anchors.fill: parent;
                        }
                    }

                    Item {
                        id: printJobOwnerName;

                        width: parent.width;
                        height: UM.Theme.getSize("monitor_tab_text_line").height;
                        anchors {
                            top: printJobName.bottom;
                            topMargin: Math.floor(UM.Theme.getSize("default_margin").height / 2);
                        }

                        Rectangle {
                            visible: !printJob;
                            color: UM.Theme.getColor("viewport_background"); // TODO: Theme!
                            height: parent.height;
                            width: parent.width / 2;
                        }
                        Label {
                            visible: printJob;
                            text: printJob ? printJob.owner : ""; // Supress QML warnings
                            font: UM.Theme.getFont("default");
                            elide: Text.ElideRight;
                            anchors.fill: parent;
                        }
                    }

                    Item {
                        id: printJobPreview;
                        property var useUltibot: false;
                        anchors {
                            top: printJobOwnerName.bottom;
                            horizontalCenter: parent.horizontalCenter;
                            topMargin: UM.Theme.getSize("default_margin").height;
                            bottom: parent.bottom;
                        }
                        width: height;

                        // Skeleton
                        Rectangle {
                            visible: !printJob;
                            anchors.fill: parent;
                            radius: UM.Theme.getSize("default_margin").width; // TODO: Theme!
                            color: UM.Theme.getColor("viewport_background"); // TODO: Theme!
                        }

                        // Actual content
                        Image {
                            id: previewImage;
                            visible: printJob;
                            source: printJob ? printJob.previewImageUrl : "";
                            opacity: printJob && printJob.state == "error" ? 0.5 : 1.0;
                            anchors.fill: parent;
                        }

                        UM.RecolorImage {
                            id: ultiBotImage;
                            anchors.centerIn: printJobPreview;
                            source: "../svg/ultibot.svg";
                            /* Since print jobs ALWAYS have an image url, we have to check if that image URL errors or
                                not in order to determine if we show the placeholder (ultibot) image instead. */
                            visible: printJob && previewImage.status == Image.Error;
                            width: printJobPreview.width;
                            height: printJobPreview.height;
                            sourceSize.width: width;
                            sourceSize.height: height;
                            color: UM.Theme.getColor("monitor_tab_placeholder_image"); // TODO: Theme!
                        }

                        UM.RecolorImage {
                            id: statusImage;
                            anchors.centerIn: printJobPreview;
                            source: printJob && printJob.state == "error" ? "../svg/aborted-icon.svg" : "";
                            visible: source != "";
                            width: 0.5 * printJobPreview.width;
                            height: 0.5 * printJobPreview.height;
                            sourceSize.width: width;
                            sourceSize.height: height;
                            color: "black";
                        }
                    }
                }

                // Divider
                Rectangle {
                    height: parent.height - 2 * UM.Theme.getSize("default_margin").height;
                    width: UM.Theme.getSize("default_lining").width;
                    color: !printJob ? UM.Theme.getColor("viewport_background") : "#e6e6e6"; // TODO: Theme!
                    anchors {
                        horizontalCenter: parent.horizontalCenter;
                        verticalCenter: parent.verticalCenter;
                    }
                }

                // Right content
                Item {
                    anchors {
                        left: parent.horizontalCenter;
                        right: parent.right;
                        top: parent.top;
                        bottom: parent.bottom;
                        margins: UM.Theme.getSize("wide_margin").width;
                    }

                    Item {
                        id: targetPrinterLabel;
                        width: parent.width;
                        height: UM.Theme.getSize("monitor_tab_text_line").height;
                        Rectangle {
                            visible: !printJob;
                            color: UM.Theme.getColor("viewport_background"); // TODO: Theme!
                            anchors.fill: parent;
                        }
                        Label {
                            visible: printJob;
                            elide: Text.ElideRight;
                            font: UM.Theme.getFont("default_bold");
                            text: {
                                if (printJob) {
                                    if (printJob.assignedPrinter == null) {
                                        if (printJob.state == "error") {
                                            return catalog.i18nc("@label", "Waiting for: Unavailable printer");
                                        }
                                        return catalog.i18nc("@label", "Waiting for: First available");
                                    } else {
                                        return catalog.i18nc("@label", "Waiting for: ") + printJob.assignedPrinter.name;
                                    }
                                }
                                return "";
                            }
                        }
                    }

                    PrinterInfoBlock {
                        printer: root.printJob.assignedPrinter;
                        printJob: root.printJob;
                        anchors.bottom: parent.bottom;
                    }
                }

                PrintJobContextMenu {
                    id: contextButton;
                    anchors {
                        right: mainContent.right;
                        rightMargin: UM.Theme.getSize("default_margin").width * 3 + root.shadowRadius;
                        top: mainContent.top;
                        topMargin: UM.Theme.getSize("default_margin").height;
                    }
                    printJob: root.printJob;
                    visible: root.printJob;
                }
            }

            Item {
                id: configChangesBox;
                width: parent.width;
                height: childrenRect.height;
                visible: printJob && printJob.configurationChanges.length !== 0;

                // Config change toggle
                Rectangle {
                    id: configChangeToggle;
                    color: {
                        if(configChangeToggleArea.containsMouse) {
                            return UM.Theme.getColor("viewport_background"); // TODO: Theme!
                        } else {
                            return "transparent";
                        }
                    }
                    width: parent.width;
                    height: UM.Theme.getSize("default_margin").height * 4; // TODO: Theme!
                    anchors {
                        left: parent.left;
                        right: parent.right;
                        top: parent.top;
                    }

                    Rectangle {
                        width: parent.width;
                        height: UM.Theme.getSize("default_lining").height;
                        color: "#e6e6e6"; // TODO: Theme!
                    }

                    UM.RecolorImage {
                        width: 23; // TODO: Theme!
                        height: 23; // TODO: Theme!
                        anchors {
                            right: configChangeToggleLabel.left;
                            rightMargin: UM.Theme.getSize("default_margin").width;
                            verticalCenter: parent.verticalCenter;
                        }
                        sourceSize.width: width;
                        sourceSize.height: height;
                        source: "../svg/warning-icon.svg";
                        color: UM.Theme.getColor("text");
                    }

                    Label {
                        id: configChangeToggleLabel;
                        anchors {
                            horizontalCenter: parent.horizontalCenter;
                            verticalCenter: parent.verticalCenter;
                        }
                        text: catalog.i18nc("@label", "Configuration change");
                    }

                    UM.RecolorImage {
                        width: 15; // TODO: Theme!
                        height: 15; // TODO: Theme!
                        anchors {
                            left: configChangeToggleLabel.right;
                            leftMargin: UM.Theme.getSize("default_margin").width;
                            verticalCenter: parent.verticalCenter;
                        }
                        sourceSize.width: width;
                        sourceSize.height: height;
                        source: {
                            if (configChangeDetails.visible) {
                                return UM.Theme.getIcon("arrow_top");
                            } else {
                                return UM.Theme.getIcon("arrow_bottom");
                            }
                        }
                        color: UM.Theme.getColor("text");
                    }

                    MouseArea {
                        id: configChangeToggleArea;
                        anchors.fill: parent;
                        hoverEnabled: true;
                        onClicked: {
                            configChangeDetails.visible = !configChangeDetails.visible;
                        }
                    }
                }

                // Config change details
                Item {
                    id: configChangeDetails;
                    width: parent.width;
                    visible: false;
                    // In case of really massive multi-line configuration changes
                    height: visible ? Math.max(UM.Theme.getSize("monitor_tab_config_override_box").height, childrenRect.height) : 0;
                    Behavior on height { NumberAnimation { duration: 100 } }
                    anchors.top: configChangeToggle.bottom;

                    Item {
                        clip: true;
                        anchors {
                            fill: parent;
                            topMargin: UM.Theme.getSize("wide_margin").height;
                            bottomMargin: UM.Theme.getSize("wide_margin").height;
                            leftMargin: UM.Theme.getSize("wide_margin").height * 4;
                            rightMargin: UM.Theme.getSize("wide_margin").height * 4;
                        }

                        Label {
                            anchors.fill: parent;
                            wrapMode: Text.WordWrap;
                            elide: Text.ElideRight;
                            font: UM.Theme.getFont("large_nonbold");
                            text: {
                                if (!printJob || printJob.configurationChanges.length === 0) {
                                    return "";
                                }
                                var topLine;
                                if (materialsAreKnown(printJob)) {
                                    topLine = catalog.i18nc("@label", "The assigned printer, %1, requires the following configuration change(s):").arg(printJob.assignedPrinter.name);
                                } else {
                                    topLine = catalog.i18nc("@label", "The printer %1 is assigned, but the job contains an unknown material configuration.").arg(printJob.assignedPrinter.name);
                                }
                                var result = "<p>" + topLine +"</p>";
                                for (var i = 0; i < printJob.configurationChanges.length; i++) {
                                    var change = printJob.configurationChanges[i];
                                    var text;
                                    switch (change.typeOfChange) {
                                        case "material_change":
                                            text = catalog.i18nc("@label", "Change material %1 from %2 to %3.").arg(change.index + 1).arg(change.originName).arg(change.targetName);
                                            break;
                                        case "material_insert":
                                            text = catalog.i18nc("@label", "Load %3 as material %1 (This cannot be overridden).").arg(change.index + 1).arg(change.targetName);
                                            break;
                                        case "print_core_change":
                                            text = catalog.i18nc("@label", "Change print core %1 from %2 to %3.").arg(change.index + 1).arg(change.originName).arg(change.targetName);
                                            break;
                                        case "buildplate_change":
                                            text = catalog.i18nc("@label", "Change build plate to %1 (This cannot be overridden).").arg(formatBuildPlateType(change.target_name));
                                            break;
                                        default:
                                            text = "";
                                    }
                                    result += "<p><b>" + text + "</b></p>"; 
                                }
                                return result;
                            }
                        }

                        Button {
                            anchors {
                                bottom: parent.bottom;
                                left: parent.left;
                            }
                            visible: {
                                var length = printJob.configurationChanges.length;
                                for (var i = 0; i < length; i++) {
                                    var typeOfChange = printJob.configurationChanges[i].typeOfChange;
                                    if (typeOfChange === "material_insert" || typeOfChange === "buildplate_change") {
                                        return false;
                                    }
                                }
                                return true;
                            }
                            text: catalog.i18nc("@label", "Override");
                            onClicked: {
                                overrideConfirmationDialog.visible = true;
                            }
                        }
                    }
                }

                MessageDialog {
                    id: overrideConfirmationDialog;
                    title: catalog.i18nc("@window:title", "Override configuration configuration and start print");
                    icon: StandardIcon.Warning;
                    text: {
                        var printJobName = formatPrintJobName(printJob.name);
                        var confirmText = catalog.i18nc("@label", "Starting a print job with an incompatible configuration could damage your 3D printer. Are you sure you want to override the configuration and print %1?").arg(printJobName);
                        return confirmText;
                    }
                    standardButtons: StandardButton.Yes | StandardButton.No;
                    Component.onCompleted: visible = false;
                    onYes: OutputDevice.forceSendJob(printJob.key);
                }
            }
        }
    }
    // Utils
    function formatPrintJobName(name) {
        var extensions = [ ".gz", ".gcode", ".ufp" ];
        for (var i = 0; i < extensions.length; i++) {
            var extension = extensions[i];
            if (name.slice(-extension.length) === extension) {
                name = name.substring(0, name.length - extension.length);
            }
        }
        return name;
    }
    function materialsAreKnown(job) {
        var conf0 = job.configuration[0];
        if (conf0 && !conf0.material.material) {
            return false;
        }
        var conf1 = job.configuration[1];
        if (conf1 && !conf1.material.material) {
            return false;
        }
        return true;
    }
    function formatBuildPlateType(buildPlateType) {
        var translationText = "";
        switch (buildPlateType) {
            case "glass":
                translationText = catalog.i18nc("@label", "Glass");
                break;
            case "aluminum":
                translationText = catalog.i18nc("@label", "Aluminum");
                break;
            default:
                translationText = null;
        }
        return translationText;
    }
}
