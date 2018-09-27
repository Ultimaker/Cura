import QtQuick 2.2
import QtQuick.Dialogs 1.1
import QtQuick.Controls 2.0
import QtQuick.Controls.Styles 1.4
import QtGraphicalEffects 1.0
import QtQuick.Layouts 1.1
import QtQuick.Dialogs 1.1
import UM 1.3 as UM

Rectangle {
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
    color: "pink";
    width: parent.width;
    height: childrenRect.height;

    Column {
        width: parent.width;
        height: childrenRect.height;
        
        // Config change toggle
        Rectangle {
            color: {
                if(configurationChangeToggle.containsMouse) {
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
                text: "Configuration change"; // TODO: i18n!
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
            color: "transparent";
            width: parent.width;
            visible: false;
            height: visible ? UM.Theme.getSize("monitor_tab_config_override_box").height : 0;
            Behavior on height { NumberAnimation { duration: 100 } }

            Rectangle {
                color: "transparent";
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
                }

                Button {
                    anchors {
                        bottom: parent.bottom;
                        left: parent.left;
                    }
                    visible: {
                        var length = root.job.configurationChanges.length;
                        for (var i = 0; i < length; i++) {
                            var typeOfChange = root.job.configurationChanges[i].typeOfChange;
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
    }

    MessageDialog {
        id: overrideConfirmationDialog;
        title: catalog.i18nc("@window:title", "Override configuration configuration and start print");
        icon: StandardIcon.Warning;
        text: {
            var printJobName = formatPrintJobName(root.job.name);
            var confirmText = catalog.i18nc("@label", "Starting a print job with an incompatible configuration could damage your 3D printer. Are you sure you want to override the configuration and print %1?").arg(printJobName);
            return confirmText;
        }
        standardButtons: StandardButton.Yes | StandardButton.No;
        Component.onCompleted: visible = false;
        onYes: OutputDevice.forceSendJob(root.job.key);
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