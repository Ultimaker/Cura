// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1

import UM 1.0 as UM

Rectangle {
    id: base;

    property Action saveAction;

    property real progress: UM.Backend.progress;
    Behavior on progress { NumberAnimation { duration: 250; } }

    property string currentDevice: "local_file"
    property bool defaultOverride: false;
    property bool defaultAmbiguous: false;

    property variant printDuration: PrintInformation.currentPrintTime;
    property real printMaterialAmount: PrintInformation.materialAmount;

    Connections {
        target: Printer;
        onOutputDevicesChanged: {
            if(!base.defaultOverride) {
                base.defaultAmbiguous = false;
                var device = null;
                for(var i in Printer.outputDevices) {
                    if(device == null) {
                        device = i;
                    } else if(Printer.outputDevices[i].priority > Printer.outputDevices[device].priority) {
                        device = i;
                    } else if(Printer.outputDevices[i].priority == Printer.outputDevices[device].priority) {
                        base.defaultAmbiguous = true;
                    }
                }

                if(device != null) {
                    base.currentDevice = device;
                }
            }
        }
    }

    Rectangle{
        id: background
        implicitWidth: base.width;
        implicitHeight: parent.height;
        color: UM.Theme.colors.save_button_background;
        border.width: UM.Theme.sizes.save_button_border.width
        border.color: UM.Theme.colors.save_button_border

        Rectangle {
            id: infoBox
            width: parent.width - UM.Theme.sizes.default_margin.width * 2;
            height: UM.Theme.sizes.save_button_slicing_bar.height

            anchors.top: parent.top
            anchors.topMargin: UM.Theme.sizes.default_margin.height;
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.sizes.default_margin.width;

            border.width: UM.Theme.sizes.save_button_border.width
            border.color: UM.Theme.colors.save_button_border
            color: UM.Theme.colors.save_button_estimated_text_background;
            Label {
                id: label;
                anchors.verticalCenter: parent.verticalCenter
                anchors.left: parent.left
                anchors.leftMargin: UM.Theme.sizes.save_button_text_margin.width;
                visible: base.progress >= 0 && base.progress < 0.99 ? false : true
                color: UM.Theme.colors.save_button_estimated_text;
                font: UM.Theme.fonts.small;
                text:
                    if(base.progress < 0) {
                        //: Save button label
                        return qsTr("Please load a 3D model");
                    } else if (base.progress < 0.99) {
                        //: Save button label
                        return qsTr("Calculating Print-time");
                    } else if (base.printDuration.days > 0 || base.progress == null){
                        return qsTr("");
                    }
                    else if (base.progress > 0.99){
                        //: Save button label
                        return qsTr("Estimated Print-time");
                    }
            }
            Label {
                id: printDurationLabel
                anchors.verticalCenter: parent.verticalCenter
                anchors.left: label.right;
                anchors.leftMargin: UM.Theme.sizes.save_button_text_margin.width;
                color: UM.Theme.colors.save_button_printtime_text;
                font: UM.Theme.fonts.small;
                visible: base.progress < 0.99 ? false : true
                text: (!base.printDuration || !base.printDuration.valid) ? "" : base.printDuration.getDisplayString(UM.DurationFormat.Long);
            }
            Label {
                id: printMaterialLabel
                anchors.verticalCenter: parent.verticalCenter
                anchors.left: printDurationLabel.right;
                anchors.leftMargin: UM.Theme.sizes.save_button_text_margin.width;
                color: base.printDuration.days > 0 ? UM.Theme.colors.save_button_estimated_text : UM.Theme.colors.save_button_printtime_text;
                font: UM.Theme.fonts.small;

                property bool mediumLengthDuration: base.printDuration.hours > 9 && base.printMaterialAmount > 9.99 && base.printDuration.days == 0
                width: mediumLengthDuration ? 50 : undefined
                elide: mediumLengthDuration ? Text.ElideRight : Text.ElideNone
                visible: base.progress < 0.99 ? false : true
                //: Print material amount save button label
                text: base.printMaterialAmount < 0 ? "" : qsTr("%1m material").arg(base.printMaterialAmount);
            }
        }
        Rectangle {
            id: infoBoxOverlay
            anchors {
                left: infoBox.left;
                top: infoBox.top;
                bottom: infoBox.bottom;
            }
            width: Math.max(infoBox.width * base.progress);
            color: UM.Theme.colors.save_button_active
            visible: base.progress > 0.99 ? false : true
        }

        Button {
            id: saveToButton
            anchors.top: infoBox.bottom
            anchors.topMargin: UM.Theme.sizes.save_button_text_margin.height;
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.sizes.default_margin.width;
            tooltip: ''
            enabled: progress >= 0.99;

            width: infoBox.width/6*4.5
            height: UM.Theme.sizes.save_button_save_to_button.height
            style: ButtonStyle {
                background: Rectangle {
                    color: !control.enabled ? UM.Theme.colors.save_button_inactive : control.hovered ? UM.Theme.colors.save_button_active_hover : UM.Theme.colors.save_button_active;
                    Label {
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.horizontalCenter: parent.horizontalCenter
                        color: UM.Theme.colors.save_button_safe_to_text;
                        font: UM.Theme.fonts.sidebar_save_to;
                        text: Printer.outputDevices[base.currentDevice].shortDescription;
                    }
                }
            }
            onClicked:
                if(base.defaultAmbiguous) {
                    devicesMenu.popup();
                } else {
                    Printer.writeToOutputDevice(base.currentDevice);
                }
        }

        Button {
            id: deviceSelectionMenu;
            anchors.top: infoBox.bottom
            anchors.topMargin: UM.Theme.sizes.save_button_text_margin.height
            anchors.right: parent.right
            anchors.rightMargin: UM.Theme.sizes.default_margin.width;
            tooltip: ''

            width: infoBox.width/6*1.3 - UM.Theme.sizes.save_button_text_margin.height;
            height: UM.Theme.sizes.save_button_save_to_button.height

            style: ButtonStyle {
                background: Rectangle {
                color: UM.Theme.colors.save_button_background;
                border.width: control.hovered ? UM.Theme.sizes.save_button_border.width : 0
                border.color: UM.Theme.colors.save_button_border
                    Rectangle {
                        id: deviceSelectionIcon
                        color: UM.Theme.colors.save_button_background;
                        anchors.left: parent.left
                        anchors.leftMargin: UM.Theme.sizes.save_button_text_margin.width / 2;
                        anchors.verticalCenter: parent.verticalCenter;
                        width: parent.height - UM.Theme.sizes.save_button_text_margin.width ;
                        height: parent.height - UM.Theme.sizes.save_button_text_margin.width;
                        UM.RecolorImage {
                            anchors.centerIn: parent;
                            width: parent.width;
                            height: parent.height;
                            sourceSize.width: width;
                            sourceSize.height: height;
                            color:  UM.Theme.colors.save_button_active
                            source: UM.Theme.icons[Printer.outputDevices[base.currentDevice].icon];
                        }
                    }
                    Label {
                        id: deviceSelectionArrow
                        anchors.right: parent.right;
                        anchors.rightMargin: UM.Theme.sizes.save_button_text_margin.height
                        anchors.verticalCenter: parent.verticalCenter;
                        text: "▼";
                        font: UM.Theme.fonts.tiny;
                        color: UM.Theme.colors.save_button_active;
                    }
                }
            }

            menu: Menu {
                id: devicesMenu;
                Instantiator {
                    model: Printer.outputDeviceNames;
                    MenuItem {
                        text: Printer.outputDevices[modelData].description;
                        checkable: true;
                        checked: base.defaultAmbiguous ? false : modelData == base.currentDevice;
                        exclusiveGroup: devicesMenuGroup;
                        onTriggered: {
                            base.defaultOverride = true;
                            base.currentDevice = modelData;
                            if(base.defaultAmbiguous) {
                                base.defaultAmbiguous = false;
                                Printer.writeToOutputDevice(modelData);
                            }
                        }
                    }
                    onObjectAdded: devicesMenu.insertItem(index, object)
                    onObjectRemoved: devicesMenu.removeItem(object)
                }
                ExclusiveGroup { id: devicesMenuGroup; }
            }
        }
    }
}