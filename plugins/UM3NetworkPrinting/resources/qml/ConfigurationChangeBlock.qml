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
    property var job: null;
    property var materialsAreKnown: {
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
    width: parent.width;
    height: childrenRect.height;

    Column {
        width: parent.width;
        height: childrenRect.height;
        
        // Config change toggle
        Rectangle {
            anchors {
                left: parent.left;
                right: parent.right;
                top: parent.top;
            }
            color: {
                if(configurationChangeToggle.containsMouse) {
                    return UM.Theme.getColor("viewport_background"); // TODO: Theme!
                } else {
                    return "transparent";
                }
            }
            height: UM.Theme.getSize("default_margin").height * 4; // TODO: Theme!
            width: parent.width;

            Rectangle {
                color: "#e6e6e6"; // TODO: Theme!
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
                    width: width;
                    height: height;
                }
                width: 23 * screenScaleFactor; // TODO: Theme!
            }

            Label {
                id: configChangeToggleLabel;
                anchors {
                    horizontalCenter: parent.horizontalCenter;
                    verticalCenter: parent.verticalCenter;
                }
                text: "Configuration change"; // TODO: i18n!
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
                id: configurationChangeToggle;
                anchors.fill: parent;
                hoverEnabled: true;
                onClicked: {
                    configChangeDetails.visible = !configChangeDetails.visible;
                }
            }
        }

        // Config change details
        Rectangle {
            id: configChangeDetails
            Behavior on height { NumberAnimation { duration: 100 } }
            color: "transparent";
            height: visible ? UM.Theme.getSize("monitor_tab_config_override_box").height : 0;
            visible: false;
            width: parent.width;

            Rectangle {
                anchors {
                    bottomMargin: UM.Theme.getSize("wide_margin").height;
                    fill: parent;
                    leftMargin: UM.Theme.getSize("wide_margin").height * 4;
                    rightMargin: UM.Theme.getSize("wide_margin").height * 4;
                    topMargin: UM.Theme.getSize("wide_margin").height;
                }
                color: "transparent";
                clip: true;

                Label {
                    anchors.fill: parent;
                    elide: Text.ElideRight;
                    font: UM.Theme.getFont("large_nonbold");
                    text: {
                        if (root.job === null) {
                            return "";
                        }
                        if (root.job.configurationChanges.length === 0) {
                            return "";
                        }
                        var topLine;
                        if (root.materialsAreKnown) {
                            topLine = catalog.i18nc("@label", "The assigned printer, %1, requires the following configuration change(s):").arg(root.job.assignedPrinter.name);
                        } else {
                            topLine = catalog.i18nc("@label", "The printer %1 is assigned, but the job contains an unknown material configuration.").arg(root.job.assignedPrinter.name);
                        }
                        var result = "<p>" + topLine +"</p>";
                        for (var i = 0; i < root.job.configurationChanges.length; i++) {
                            var change = root.job.configurationChanges[i];
                            var text;
                            switch (change.typeOfChange) {
                                case 'material_change':
                                    text = catalog.i18nc("@label", "Change material %1 from %2 to %3.").arg(change.index + 1).arg(change.originName).arg(change.targetName);
                                    break;
                                case 'material_insert':
                                    text = catalog.i18nc("@label", "Load %3 as material %1 (This cannot be overridden).").arg(change.index + 1).arg(change.targetName);
                                    break;
                                case 'print_core_change':
                                    text = catalog.i18nc("@label", "Change print core %1 from %2 to %3.").arg(change.index + 1).arg(change.originName).arg(change.targetName);
                                    break;
                                case 'buildplate_change':
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
                    onClicked: {
                        overrideConfirmationDialog.visible = true;
                    }
                    text: catalog.i18nc("@label", "Override");
                    visible: {
                        if (root.job & root.job.configurationChanges) {
                            var length = root.job.configurationChanges.length;
                            for (var i = 0; i < length; i++) {
                                var typeOfChange = root.job.configurationChanges[i].typeOfChange;
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
    }

    MessageDialog {
        id: overrideConfirmationDialog;
        Component.onCompleted: visible = false;
        icon: StandardIcon.Warning;
        onYes: OutputDevice.forceSendJob(root.job.key);
        standardButtons: StandardButton.Yes | StandardButton.No;
        text: {
            if (!root.job) {
                return "";
            }
            var printJobName = formatPrintJobName(root.job.name);
            var confirmText = catalog.i18nc("@label", "Starting a print job with an incompatible configuration could damage your 3D printer. Are you sure you want to override the configuration and print %1?").arg(printJobName);
            return confirmText;
        }
        title: catalog.i18nc("@window:title", "Override configuration configuration and start print");
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
            case 'glass':
                translationText = catalog.i18nc("@label", "Glass");
                break;
            case 'aluminum':
                translationText = catalog.i18nc("@label", "Aluminum");
                break;
            default:
                translationText = null;
        }
        return translationText;
    }
}