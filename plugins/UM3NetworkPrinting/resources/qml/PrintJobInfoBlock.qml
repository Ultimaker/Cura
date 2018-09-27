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
            color: "#3F000000"  // 25% shadow
        }

        Column {
            width: parent.width;
            height: childrenRect.height;

            // Main content
            Rectangle {
                id: mainContent;
                color: root.debug ? "red" : "transparent";
                width: parent.width;
                height: 200; // TODO: Theme!

                // Left content
                Rectangle {
                    color: root.debug ? "lightblue" : "transparent";
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
                            visible: !root.printJob;
                            color: UM.Theme.getColor("viewport_background"); // TODO: Theme!
                            height: parent.height;
                            width: parent.width / 3;
                        }
                        Label {
                            visible: root.printJob;
                            text: root.printJob ? root.printJob.name : ""; // Supress QML warnings
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
                            visible: !root.printJob;
                            color: UM.Theme.getColor("viewport_background"); // TODO: Theme!
                            height: parent.height;
                            width: parent.width / 2;
                        }
                        Label {
                            visible: root.printJob;
                            text: root.printJob ? root.printJob.owner : ""; // Supress QML warnings
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
                            visible: !root.printJob;
                            anchors.fill: parent;
                            radius: UM.Theme.getSize("default_margin").width; // TODO: Theme!
                            color: UM.Theme.getColor("viewport_background"); // TODO: Theme!
                        }

                        // Actual content
                        Image {
                            id: previewImage;
                            visible: root.printJob;
                            source: root.printJob.previewImageUrl;
                            opacity: root.printJob.state == "error" ? 0.5 : 1.0;
                            anchors.fill: parent;
                        }

                        UM.RecolorImage {
                            id: ultiBotImage;
                            anchors.centerIn: printJobPreview;
                            source: "../svg/ultibot.svg";
                            /* Since print jobs ALWAYS have an image url, we have to check if that image URL errors or
                                not in order to determine if we show the placeholder (ultibot) image instead. */
                            visible: root.printJob && previewImage.status == Image.Error;
                            width: printJobPreview.width;
                            height: printJobPreview.height;
                            sourceSize.width: width;
                            sourceSize.height: height;
                            color: UM.Theme.getColor("monitor_tab_placeholder_image"); // TODO: Theme!
                        }

                        UM.RecolorImage {
                            id: statusImage;
                            anchors.centerIn: printJobPreview;
                            source: printJob.state == "error" ? "../svg/aborted-icon.svg" : "";
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
                    color: !root.printJob ? UM.Theme.getColor("viewport_background") : "#e6e6e6"; // TODO: Theme!
                    anchors {
                        horizontalCenter: parent.horizontalCenter;
                        verticalCenter: parent.verticalCenter;
                    }
                }

                // Right content
                Rectangle {
                    color: root.debug ? "blue" : "transparent";
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
                            visible: !root.printJob;
                            color: UM.Theme.getColor("viewport_background"); // TODO: Theme!
                            anchors.fill: parent;
                        }
                        Label {
                            visible: root.printJob;
                            elide: Text.ElideRight;
                            font: UM.Theme.getFont("default_bold");
                            text: {
                                if (root.printJob.assignedPrinter == null) {
                                    if (root.printJob.state == "error") {
                                        return catalog.i18nc("@label", "Waiting for: Unavailable printer");
                                    }
                                    return catalog.i18nc("@label", "Waiting for: First available");
                                } else {
                                    return catalog.i18nc("@label", "Waiting for: ") + root.printJob.assignedPrinter.name;
                                }
                            }
                        }
                    }

                    // Printer family pills
                    Row {
                        id: printerFamilyPills;
                        visible: root.printJob;
                        spacing: Math.round(0.5 * UM.Theme.getSize("default_margin").width);
                        anchors {
                            left: parent.left;
                            right: parent.right;
                            bottom: extrudersInfo.top;
                            bottomMargin: UM.Theme.getSize("default_margin").height;
                        }
                        height: childrenRect.height;
                        Repeater {
                            model: printJob.compatibleMachineFamilies;
                            delegate: PrinterFamilyPill {
                                text: modelData;
                                color: UM.Theme.getColor("viewport_background"); // TODO: Theme!
                                padding: 3 * screenScaleFactor; // TODO: Theme!
                            }
                        }
                    }

                    // Print core & material config
                    Row {
                        id: extrudersInfo;
                        anchors {
                            bottom: parent.bottom;
                            left: parent.left;
                            right: parent.right;
                            rightMargin: UM.Theme.getSize("default_margin").width;
                        }
                        height: childrenRect.height;
                        spacing: UM.Theme.getSize("default_margin").width;
                        PrintCoreConfiguration {
                            id: leftExtruderInfo;
                            width: Math.round(parent.width / 2) * screenScaleFactor;
                            printCoreConfiguration: root.printJob !== null ? printJob.configuration.extruderConfigurations[0] : null;
                        }
                        PrintCoreConfiguration {
                            id: rightExtruderInfo;
                            width: Math.round(parent.width / 2) * screenScaleFactor;
                            printCoreConfiguration: root.printJob !== null ? printJob.configuration.extruderConfigurations[1] : null;
                        }
                    }
                }
            }

            Rectangle {
                id: configChangesBox;
                width: parent.width;
                height: childrenRect.height;
                visible: root.printJob && root.printJob.configurationChanges.length !== 0;

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
                        id: configChangeToggleArea;
                        anchors.fill: parent;
                        hoverEnabled: true;
                        onClicked: {
                            configChangeDetails.visible = !configChangeDetails.visible;
                        }
                    }
                }

                // Config change details
                Rectangle {
                    id: configChangeDetails;
                    color: "transparent";
                    width: parent.width;
                    visible: false;
                    // In case of really massive multi-line configuration changes
                    height: visible ? Math.max(UM.Theme.getSize("monitor_tab_config_override_box").height, childrenRect.height) : 0;
                    Behavior on height { NumberAnimation { duration: 100 } }
                    anchors.top: configChangeToggle.bottom;

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
                                if (root.printJob.configurationChanges.length === 0) {
                                    return "";
                                }
                                var topLine;
                                if (materialsAreKnown(root.printJob)) {
                                    topLine = catalog.i18nc("@label", "The assigned printer, %1, requires the following configuration change(s):").arg(root.printJob.assignedPrinter.name);
                                } else {
                                    topLine = catalog.i18nc("@label", "The printer %1 is assigned, but the job contains an unknown material configuration.").arg(root.printJob.assignedPrinter.name);
                                }
                                var result = "<p>" + topLine +"</p>";
                                for (var i = 0; i < root.printJob.configurationChanges.length; i++) {
                                    var change = root.printJob.configurationChanges[i];
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
                                var length = root.printJob.configurationChanges.length;
                                for (var i = 0; i < length; i++) {
                                    var typeOfChange = root.printJob.configurationChanges[i].typeOfChange;
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
                        var printJobName = formatPrintJobName(root.printJob.name);
                        var confirmText = catalog.i18nc("@label", "Starting a print job with an incompatible configuration could damage your 3D printer. Are you sure you want to override the configuration and print %1?").arg(printJobName);
                        return confirmText;
                    }
                    standardButtons: StandardButton.Yes | StandardButton.No;
                    Component.onCompleted: visible = false;
                    onYes: OutputDevice.forceSendJob(root.printJob.key);
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



// Item
// {
//     id: base

//     function haveAlert() {
//         return printJob.configurationChanges.length !== 0;
//     }

//     function alertHeight() {
//         return haveAlert() ? 230 : 0;
//     }

//     function alertText() {
//         if (printJob.configurationChanges.length === 0) {
//             return "";
//         }

//         var topLine;
//         if (materialsAreKnown(printJob)) {
//             topLine = catalog.i18nc("@label", "The assigned printer, %1, requires the following configuration change(s):").arg(printJob.assignedPrinter.name);
//         } else {
//             topLine = catalog.i18nc("@label", "The printer %1 is assigned, but the job contains an unknown material configuration.").arg(printJob.assignedPrinter.name);
//         }
//         var result = "<p>" + topLine +"</p>";

//         for (var i=0; i<printJob.configurationChanges.length; i++) {
//             var change = printJob.configurationChanges[i];
//             var text = "";
//             if (change.typeOfChange === 'material_change') {
//                 text = catalog.i18nc("@label", "Change material %1 from %2 to %3.").arg(change.index + 1).arg(change.originName).arg(change.targetName);
//             } else if (change.typeOfChange === 'material_insert') {
//                 text = catalog.i18nc("@label", "Load %3 as material %1 (This cannot be overridden).").arg(change.index + 1).arg(change.targetName);
//             } else if (change.typeOfChange === 'print_core_change') {
//                 text = catalog.i18nc("@label", "Change print core %1 from %2 to %3.").arg(change.index + 1).arg(change.originName).arg(change.targetName);
//             } else if (change.typeOfChange === 'buildplate_change') {
//                 var target_name = formatBuildPlateType(change.target_name);
//                 text = catalog.i18nc("@label", "Change build plate to %1 (This cannot be overridden).").arg(target_name);
//             }
//             result += "<p><b>" + text + "</b></p>"; 
//         }
//         return result;
//     }

//     function materialsAreKnown(printJob) {
//         var conf0 = printJob.configuration[0];
//         if (conf0 && !conf0.material.material) {
//             return false;
//         }

//         var conf1 = printJob.configuration[1];
//         if (conf1 && !conf1.material.material) {
//             return false;
//         }

//         return true;
//     }

//     function formatBuildPlateType(buildPlateType) {
//         var translationText = "";

//         switch (buildPlateType) {
//             case 'glass':
//                 translationText = catalog.i18nc("@label", "Glass");
//                 break;
//             case 'aluminum':
//                 translationText = catalog.i18nc("@label", "Aluminum");
//                 break;
//             default:
//                 translationText = null;
//         }
//         return translationText;
//     }

//     function formatPrintJobName(name) {
//         var extensionsToRemove = [
//             '.gz',
//             '.gcode',
//             '.ufp'
//         ];

//         for (var i = 0; i < extensionsToRemove.length; i++) {
//             var extension = extensionsToRemove[i];

//             if (name.slice(-extension.length) === extension) {
//                 name = name.substring(0, name.length - extension.length);
//             }
//         }

//         return name;
//     }

//     function isPrintJobForcable(printJob) {
//         var forcable = true;

//         for (var i = 0; i < printJob.configurationChanges.length; i++) {
//             var typeOfChange = printJob.configurationChanges[i].typeOfChange;
//             if (typeOfChange === 'material_insert' || typeOfChange === 'buildplate_change') {
//                 forcable = false;
//             }
//         }

//         return forcable;
//     }

//     property var cardHeight: 175

//     height: (cardHeight + alertHeight()) * screenScaleFactor
//     property var printJob: null
//     property var shadowRadius: 5 * screenScaleFactor
//     function getPrettyTime(time)
//     {
//         return OutputDevice.formatDuration(time)
//     }

//     width: parent.width

//     UM.I18nCatalog
//     {
//         id: catalog
//         name: "cura"
//     }

//     Rectangle
//     {
//         id: background

//         height: (cardHeight + alertHeight()) * screenScaleFactor

//         anchors
//         {
//             top: parent.top
//             topMargin: 3 * screenScaleFactor
//             left: parent.left
//             leftMargin: base.shadowRadius
//             rightMargin: base.shadowRadius
//             right: parent.right
//             //bottom: parent.bottom - alertHeight() * screenScaleFactor
//             bottomMargin: base.shadowRadius
//         }

//         layer.enabled: true
//         layer.effect: DropShadow
//         {
//             radius: base.shadowRadius
//             verticalOffset: 2 * screenScaleFactor
//             color: "#3F000000"  // 25% shadow
//         }

//     Rectangle
//     {
//         height: cardHeight * screenScaleFactor

//         anchors
//         {
//             top: parent.top
//             left: parent.left
//             right: parent.right
//             // bottom: parent.bottom
//         }

//         Item
//         {
//             // Content on the left of the infobox
//             anchors
//             {
//                 top: parent.top
//                 bottom: parent.bottom
//                 left: parent.left
//                 right: parent.horizontalCenter
//                 margins: UM.Theme.getSize("wide_margin").width
//                 rightMargin: UM.Theme.getSize("default_margin").width
//             }

//             Label
//             {
//                 id: printJobName
//                 text: printJob.name
//                 font: UM.Theme.getFont("default_bold")
//                 width: parent.width
//                 elide: Text.ElideRight
//             }

//             Label
//             {
//                 id: ownerName
//                 anchors.top: printJobName.bottom
//                 text: printJob.owner
//                 font: UM.Theme.getFont("default")
//                 opacity: 0.6
//                 width: parent.width
//                 elide: Text.ElideRight
//             }

//             Image
//             {
//                 id: printJobPreview
//                 source: printJob.previewImageUrl
//                 anchors.top: ownerName.bottom
//                 anchors.horizontalCenter: parent.horizontalCenter
//                 anchors.bottom: totalTimeLabel.bottom
//                 width: height
//                 opacity: printJob.state == "error" ? 0.5 : 1.0
//             }

//             UM.RecolorImage
//             {
//                 id: statusImage
//                 anchors.centerIn: printJobPreview
//                 source: printJob.state == "error" ? "../svg/aborted-icon.svg" : ""
//                 visible: source != ""
//                 width: 0.5 * printJobPreview.width
//                 height: 0.5 * printJobPreview.height
//                 sourceSize.width: width
//                 sourceSize.height: height
//                 color: "black"
//             }

//             Label
//             {
//                 id: totalTimeLabel
//                 anchors.bottom: parent.bottom
//                 anchors.right: parent.right
//                 font: UM.Theme.getFont("default")
//                 text: printJob != null ? getPrettyTime(printJob.timeTotal) : ""
//                 elide: Text.ElideRight
//             }
//         }

//         Item
//         {
//             // Content on the right side of the infobox.
//             anchors
//             {
//                 top: parent.top
//                 bottom: parent.bottom
//                 left: parent.horizontalCenter
//                 right: parent.right
//                 margins: 2 * UM.Theme.getSize("default_margin").width
//                 leftMargin: UM.Theme.getSize("default_margin").width
//                 rightMargin: UM.Theme.getSize("default_margin").width / 2
//             }

//             Label
//             {
//                 id: targetPrinterLabel
//                 elide: Text.ElideRight
//                 font: UM.Theme.getFont("default_bold")
//                 text:
//                 {
//                     if(printJob.assignedPrinter == null)
//                     {
//                         if(printJob.state == "error")
//                         {
//                             return catalog.i18nc("@label", "Waiting for: Unavailable printer")
//                         }
//                         return catalog.i18nc("@label", "Waiting for: First available")
//                     }
//                     else
//                     {
//                         return catalog.i18nc("@label", "Waiting for: ") + printJob.assignedPrinter.name
//                     }

//                 }

//                 anchors
//                 {
//                     left: parent.left
//                     right: contextButton.left
//                     rightMargin: UM.Theme.getSize("default_margin").width
//                 }
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
//                         id: sendToTopButton
//                         text: catalog.i18nc("@label", "Move to top")
//                         onClicked:
//                         {
//                             sendToTopConfirmationDialog.visible = true;
//                             popup.close();
//                         }
//                         width: parent.width
//                         enabled: OutputDevice.queuedPrintJobs[0].key != printJob.key
//                         visible: enabled
//                         anchors.top: parent.top
//                         anchors.topMargin: 18 * screenScaleFactor
//                         height: visible ? 39 * screenScaleFactor : 0 * screenScaleFactor
//                         hoverEnabled: true
//                         background: Rectangle
//                         {
//                             opacity: sendToTopButton.down || sendToTopButton.hovered ? 1 : 0
//                             color: UM.Theme.getColor("viewport_background")
//                         }
//                         contentItem: Label
//                         {
//                             text: sendToTopButton.text
//                             horizontalAlignment: Text.AlignLeft
//                             verticalAlignment: Text.AlignVCenter
//                         }
//                     }

//                     MessageDialog
//                     {
//                         id: sendToTopConfirmationDialog
//                         title: catalog.i18nc("@window:title", "Move print job to top")
//                         icon: StandardIcon.Warning
//                         text: catalog.i18nc("@label %1 is the name of a print job.", "Are you sure you want to move %1 to the top of the queue?").arg(printJob.name)
//                         standardButtons: StandardButton.Yes | StandardButton.No
//                         Component.onCompleted: visible = false
//                         onYes: OutputDevice.sendJobToTop(printJob.key)
//                     }

//                     Button
//                     {
//                         id: deleteButton
//                         text: catalog.i18nc("@label", "Delete")
//                         onClicked:
//                         {
//                             deleteConfirmationDialog.visible = true;
//                             popup.close();
//                         }
//                         width: parent.width
//                         height: 39 * screenScaleFactor
//                         anchors.top: sendToTopButton.bottom
//                         hoverEnabled: true
//                         background: Rectangle
//                         {
//                             opacity: deleteButton.down || deleteButton.hovered ? 1 : 0
//                             color: UM.Theme.getColor("viewport_background")
//                         }
//                         contentItem: Label
//                         {
//                             text: deleteButton.text
//                             horizontalAlignment: Text.AlignLeft
//                             verticalAlignment: Text.AlignVCenter
//                         }
//                     }

//                     MessageDialog
//                     {
//                         id: deleteConfirmationDialog
//                         title: catalog.i18nc("@window:title", "Delete print job")
//                         icon: StandardIcon.Warning
//                         text: catalog.i18nc("@label %1 is the name of a print job.", "Are you sure you want to delete %1?").arg(printJob.name)
//                         standardButtons: StandardButton.Yes | StandardButton.No
//                         Component.onCompleted: visible = false
//                         onYes: OutputDevice.deleteJobFromQueue(printJob.key)
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

//             Row
//             {
//                 id: printerFamilyPills
//                 spacing: 0.5 * UM.Theme.getSize("default_margin").width
//                 anchors
//                 {
//                     left: parent.left
//                     right: parent.right
//                     bottom: extrudersInfo.top
//                     bottomMargin: UM.Theme.getSize("default_margin").height
//                 }
//                 height: childrenRect.height
//                 Repeater
//                 {
//                     model: printJob.compatibleMachineFamilies

//                     delegate: PrinterFamilyPill
//                     {
//                         text: modelData
//                         color: UM.Theme.getColor("viewport_background")
//                         padding: 3 * screenScaleFactor
//                     }
//                 }
//             }
//             // PrintCore && Material config
//             Row
//             {
//                 id: extrudersInfo
//                 anchors.bottom: parent.bottom

//                 anchors
//                 {
//                     left: parent.left
//                     right: parent.right
//                 }
//                 height: childrenRect.height

//                 spacing: UM.Theme.getSize("default_margin").width

//                 PrintCoreConfiguration
//                 {
//                     id: leftExtruderInfo
//                     width: Math.round(parent.width / 2) * screenScaleFactor
//                     printCoreConfiguration: printJob.configuration.extruderConfigurations[0]
//                 }

//                 PrintCoreConfiguration
//                 {
//                     id: rightExtruderInfo
//                     width: Math.round(parent.width / 2) * screenScaleFactor
//                     printCoreConfiguration: printJob.configuration.extruderConfigurations[1]
//                 }
//             }

//         }
//         }
//         Rectangle
//         {
//             height: cardHeight * screenScaleFactor
//             color: UM.Theme.getColor("viewport_background")
//             width: 2 * screenScaleFactor
//             anchors.top: parent.top
//             anchors.margins: UM.Theme.getSize("default_margin").height
//             anchors.horizontalCenter: parent.horizontalCenter
//         }

//         // Alert / Configuration change box
//         Rectangle
//         {
//             height: alertHeight() * screenScaleFactor

//             anchors.left: parent.left
//             anchors.right: parent.right
//             anchors.bottom: parent.bottom

// color: "#ff00ff"
//             ColumnLayout
//             {
//                 anchors.fill: parent
//                 RowLayout
//                 {
//                     Item
//                     {
//                         Layout.fillWidth: true
//                     }

//                     Label
//                     {
//                         font: UM.Theme.getFont("default_bold")
//                         text: "Configuration change"
//                     }

//                     UM.RecolorImage
//                     {
//                         id: collapseIcon
//                         width: 15
//                         height: 15
//                         sourceSize.width: width
//                         sourceSize.height: height

//                         // FIXME
//                         source: base.collapsed ?  UM.Theme.getIcon("arrow_left") : UM.Theme.getIcon("arrow_bottom")
//                         color: "black"
//                     }

//                     Item
//                     {
//                         Layout.fillWidth: true
//                     }

//                 }

//                 Rectangle
//                 {
//                     Layout.fillHeight: true
//                     Layout.fillWidth: true
// color: "red"

//                     Rectangle
//                     {
// color: "green"
//                         width: childrenRect.width

//                         anchors.horizontalCenter: parent.horizontalCenter
//                         anchors.top: parent.top
//                         anchors.bottom: parent.bottom

//                         ColumnLayout
//                         {
//                             width: childrenRect.width

//                             anchors.top: parent.top
//                             anchors.bottom: parent.bottom

//                             Text
//                             {
//                                 Layout.alignment: Qt.AlignTop

//                                 textFormat: Text.StyledText
//                                 font: UM.Theme.getFont("default_bold")
//                                 text: alertText()
//                             }

//                             Button
//                             {
//                                 visible: isPrintJobForcable(printJob)
//                                 text: catalog.i18nc("@label", "Override")
//                                 onClicked: {
//                                     overrideConfirmationDialog.visible = true;
//                                 }
//                             }

//                             // Spacer
//                             Item
//                             {
//                                 Layout.fillHeight: true
//                             }
//                         }
//                     }
//                 }
//             }
//         }

//         MessageDialog
//         {
//             id: overrideConfirmationDialog
//             title: catalog.i18nc("@window:title", "Override configuration configuration and start print")
//             icon: StandardIcon.Warning
//             text: {
//                 var printJobName = formatPrintJobName(printJob.name);
//                 var confirmText = catalog.i18nc("@label", "Starting a print job with an incompatible configuration could damage your 3D printer. Are you sure you want to override the configuration and print %1?").arg(printJobName);
//                 return confirmText;
//             }

//             standardButtons: StandardButton.Yes | StandardButton.No
//             Component.onCompleted: visible = false
//             onYes: OutputDevice.forceSendJob(printJob.key)
//         }        
//     }
// }