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
    id: root;
    property var shadowRadius: UM.Theme.getSize("monitor_shadow_radius").width;
    property var shadowOffset: 2 * screenScaleFactor;
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
        // 5px margin, but shifted 2px vertically because of the shadow
        anchors {
            bottomMargin: root.shadowRadius + root.shadowOffset;
            leftMargin: root.shadowRadius;
            rightMargin: root.shadowRadius;
            topMargin: root.shadowRadius - root.shadowOffset;
        }
        color: UM.Theme.getColor("monitor_card_background");
        height: childrenRect.height;
        layer.enabled: true
        layer.effect: DropShadow {
            radius: root.shadowRadius
            verticalOffset: 2 * screenScaleFactor
            color: "#3F000000" // 25% shadow
        }
        width: parent.width - shadowRadius * 2;

        Column {
            height: childrenRect.height;
            width: parent.width;

            // Main content
            Item {
                id: mainContent;
                height: 200 * screenScaleFactor; // TODO: Theme!
                width: parent.width;

                // Left content
                Item {
                    anchors {
                        bottom: parent.bottom;
                        left: parent.left;
                        margins: UM.Theme.getSize("wide_margin").width;
                        right: parent.horizontalCenter;
                        top: parent.top;
                    }

                    Item {
                        id: printJobName;
                        width: parent.width;
                        height: UM.Theme.getSize("monitor_text_line").height;

                        Rectangle {
                            color: UM.Theme.getColor("monitor_skeleton_fill");
                            height: parent.height;
                            visible: !printJob;
                            width: Math.round(parent.width / 3);
                        }
                        Label {
                            anchors.fill: parent;
                            color: UM.Theme.getColor("text");
                            elide: Text.ElideRight;
                            font: UM.Theme.getFont("default_bold");
                            text: printJob && printJob.name ? printJob.name : ""; // Supress QML warnings
                            visible: printJob;
                        }
                    }

                    Item {
                        id: printJobOwnerName;
                        anchors {
                            top: printJobName.bottom;
                            topMargin: Math.floor(UM.Theme.getSize("default_margin").height / 2);
                        }
                        height: UM.Theme.getSize("monitor_text_line").height;
                        width: parent.width;

                        Rectangle {
                            color: UM.Theme.getColor("monitor_skeleton_fill");
                            height: parent.height;
                            visible: !printJob;
                            width: Math.round(parent.width / 2);
                        }
                        Label {
                            anchors.fill: parent;
                            color: UM.Theme.getColor("text");
                            elide: Text.ElideRight;
                            font: UM.Theme.getFont("default");
                            text: printJob ? printJob.owner : ""; // Supress QML warnings
                            visible: printJob;
                        }
                    }

                    Item {
                        id: printJobPreview;
                        property var useUltibot: false;
                        anchors {
                            bottom: parent.bottom;
                            horizontalCenter: parent.horizontalCenter;
                            top: printJobOwnerName.bottom;
                            topMargin: UM.Theme.getSize("default_margin").height;
                        }
                        width: height;

                        // Skeleton
                        Rectangle {
                            anchors.fill: parent;
                            color: UM.Theme.getColor("monitor_skeleton_fill");
                            radius: UM.Theme.getSize("default_margin").width;
                            visible: !printJob;
                        }

                        // Actual content
                        Image {
                            id: previewImage;
                            anchors.fill: parent;
                            opacity: printJob && printJob.state == "error" ? 0.5 : 1.0;
                            source: printJob ? printJob.previewImageUrl : "";
                            visible: printJob;
                        }

                        UM.RecolorImage {
                            id: ultiBotImage;
                            
                            anchors.centerIn: printJobPreview;
                            color: UM.Theme.getColor("monitor_placeholder_image");
                            height: printJobPreview.height;
                            source: "../svg/ultibot.svg";
                            sourceSize {
                                height: height;
                                width: width;
                            }
                            /* Since print jobs ALWAYS have an image url, we have to check if that image URL errors or
                                not in order to determine if we show the placeholder (ultibot) image instead. */
                            visible: printJob && previewImage.status == Image.Error;
                            width: printJobPreview.width;
                        }

                        UM.RecolorImage {
                            id: statusImage;
                            anchors.centerIn: printJobPreview;
                            color: UM.Theme.getColor("monitor_image_overlay");
                            height: 0.5 * printJobPreview.height;
                            source: printJob && printJob.state == "error" ? "../svg/aborted-icon.svg" : "";
                            sourceSize {
                                height: height;
                                width: width;
                            }
                            visible: source != "";
                            width: 0.5 * printJobPreview.width;
                        }
                    }

                    Label {
                        id: totalTimeLabel;
                        anchors {
                            bottom: parent.bottom;
                            right: parent.right;
                        }
                        color: UM.Theme.getColor("text");
                        elide: Text.ElideRight;
                        font: UM.Theme.getFont("default");
                        text: printJob ? OutputDevice.formatDuration(printJob.timeTotal) : "";
                    }
                }

                // Divider
                Rectangle {
                    anchors {
                        horizontalCenter: parent.horizontalCenter;
                        verticalCenter: parent.verticalCenter;
                    }
                    color: !printJob ? UM.Theme.getColor("monitor_skeleton_fill") : UM.Theme.getColor("monitor_lining_light");
                    height: parent.height - 2 * UM.Theme.getSize("default_margin").height;
                    width: UM.Theme.getSize("default_lining").width;
                }

                // Right content
                Item {
                    anchors {
                        bottom: parent.bottom;
                        left: parent.horizontalCenter;
                        margins: UM.Theme.getSize("wide_margin").width;
                        right: parent.right;
                        top: parent.top;
                    }

                    Item {
                        id: targetPrinterLabel;
                        height: UM.Theme.getSize("monitor_text_line").height;
                        width: parent.width;

                        Rectangle {
                            visible: !printJob;
                            color: UM.Theme.getColor("monitor_skeleton_fill");
                            anchors.fill: parent;
                        }

                        Label {
                            color: UM.Theme.getColor("text");
                            elide: Text.ElideRight;
                            font: UM.Theme.getFont("default_bold");
                            text: {
                                if (printJob !== null) {
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
                            visible: printJob;
                        }
                    }

                    PrinterInfoBlock {
                        anchors.bottom: parent.bottom;
                        printer: root.printJon && root.printJob.assignedPrinter;
                        printJob: root.printJob;
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
                height: childrenRect.height;
                visible: printJob && printJob.configurationChanges.length !== 0;
                width: parent.width;

                // Config change toggle
                Rectangle {
                    id: configChangeToggle;
                    color: {
                        if (configChangeToggleArea.containsMouse) {
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
                        color: !printJob ? UM.Theme.getColor("monitor_skeleton_fill") : UM.Theme.getColor("monitor_lining_light");
                        height: UM.Theme.getSize("default_lining").height;
                        width: parent.width;
                    }

                    UM.RecolorImage {
                        anchors {
                            right: configChangeToggleLabel.left;
                            rightMargin: UM.Theme.getSize("default_margin").width;
                            verticalCenter: parent.verticalCenter;
                        }
                        color: UM.Theme.getColor("text");
                        height: 23 * screenScaleFactor; // TODO: Theme!
                        source: "../svg/warning-icon.svg";
                        sourceSize {
                            height: height;
                            width: width;
                        }
                        width: 23 * screenScaleFactor; // TODO: Theme!
                    }

                    Label {
                        id: configChangeToggleLabel;
                        anchors {
                            horizontalCenter: parent.horizontalCenter;
                            verticalCenter: parent.verticalCenter;
                        }
                        color: UM.Theme.getColor("text");
                        font: UM.Theme.getFont("default");
                        text: catalog.i18nc("@label", "Configuration change");
                    }

                    UM.RecolorImage {
                        anchors {
                            left: configChangeToggleLabel.right;
                            leftMargin: UM.Theme.getSize("default_margin").width;
                            verticalCenter: parent.verticalCenter;
                        }
                        color: UM.Theme.getColor("text");
                        height: 15 * screenScaleFactor; // TODO: Theme!
                        source: {
                            if (configChangeDetails.visible) {
                                return UM.Theme.getIcon("arrow_top");
                            } else {
                                return UM.Theme.getIcon("arrow_bottom");
                            }
                        }
                        sourceSize {
                            width: width;
                            height: height;
                        }
                        width: 15 * screenScaleFactor; // TODO: Theme!
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
                    anchors.top: configChangeToggle.bottom;
                    Behavior on height { NumberAnimation { duration: 100 } }
                    // In case of really massive multi-line configuration changes
                    height: visible ? Math.max(UM.Theme.getSize("monitor_config_override_box").height, childrenRect.height) : 0;
                    visible: false;
                    width: parent.width;

                    Item {
                        anchors {
                            bottomMargin: UM.Theme.getSize("wide_margin").height;
                            fill: parent;
                            leftMargin: UM.Theme.getSize("wide_margin").height * 4;
                            rightMargin: UM.Theme.getSize("wide_margin").height * 4;
                            topMargin: UM.Theme.getSize("wide_margin").height;
                        }
                        clip: true;

                        Label {
                            anchors.fill: parent;
                            elide: Text.ElideRight;
                            color: UM.Theme.getColor("text");
                            font: UM.Theme.getFont("default");
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
                            wrapMode: Text.WordWrap;
                        }

                        Button {
                            anchors {
                                bottom: parent.bottom;
                                left: parent.left;
                            }
                            background: Rectangle {
                                border {
                                    color: UM.Theme.getColor("monitor_lining_heavy");
                                    width: UM.Theme.getSize("default_lining").width;
                                }
                                color: parent.hovered ? UM.Theme.getColor("monitor_card_background_inactive") : UM.Theme.getColor("monitor_card_background");
                                implicitHeight: UM.Theme.getSize("default_margin").height * 3;
                                implicitWidth: UM.Theme.getSize("default_margin").height * 8;
                            }
                            contentItem: Label {
                                color: UM.Theme.getColor("text");
                                font: UM.Theme.getFont("medium");
                                horizontalAlignment: Text.AlignHCenter;
                                text: parent.text;
                                verticalAlignment: Text.AlignVCenter;
                            }
                            onClicked: {
                                overrideConfirmationDialog.visible = true;
                            }
                            text: catalog.i18nc("@label", "Override");
                            visible: {
                                if (printJob && printJob.configurationChanges) {
                                    var length = printJob.configurationChanges.length;
                                    for (var i = 0; i < length; i++) {
                                        var typeOfChange = printJob.configurationChanges[i].typeOfChange;
                                        if (typeOfChange === "material_insert" || typeOfChange === "buildplate_change") {
                                            return false;
                                        }
                                    }
                                }
                                return true;
                            }
                        }
                    }
                }

                MessageDialog {
                    id: overrideConfirmationDialog;
                    Component.onCompleted: visible = false;
                    icon: StandardIcon.Warning;
                    onYes: OutputDevice.forceSendJob(printJob.key);
                    standardButtons: StandardButton.Yes | StandardButton.No;
                    text: {
                        if (!printJob) {
                            return "";
                        }
                        var printJobName = formatPrintJobName(printJob.name);
                        var confirmText = catalog.i18nc("@label", "Starting a print job with an incompatible configuration could damage your 3D printer. Are you sure you want to override the configuration and print %1?").arg(printJobName);
                        return confirmText;
                    }
                    title: catalog.i18nc("@window:title", "Override configuration configuration and start print");
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
