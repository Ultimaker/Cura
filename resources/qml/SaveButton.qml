// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1

import UM 1.1 as UM

Rectangle {
    id: base;
    UM.I18nCatalog { id: catalog; name:"cura"}

    property real progress: UM.Backend.progress;
    property int backendState: UM.Backend.state;

    property bool activity: Printer.getPlatformActivity;
    //Behavior on progress { NumberAnimation { duration: 250; } }
    property int totalHeight: childrenRect.height + UM.Theme.getSize("default_margin").height
    property string fileBaseName
    property string statusText:
    {
        if(!activity)
        {
            return catalog.i18nc("@label:PrintjobStatus", "Please load a 3d model");
        }

        if(base.backendState == 1)
        {
            return catalog.i18nc("@label:PrintjobStatus", "Preparing to slice...");
        }
        else if(base.backendState == 2)
        {
            return catalog.i18nc("@label:PrintjobStatus", "Slicing...");
        }
        else if(base.backendState == 3)
        {
            return catalog.i18nc("@label:PrintjobStatus %1 is target operation","Ready to %1").arg(UM.OutputDeviceManager.activeDeviceShortDescription);
        }
        else if(base.backendState == 4)
        {
            return catalog.i18nc("@label:PrintjobStatus", "Unable to Slice")
        }
    }

    Label {
        id: statusLabel
        width: parent.width - 2 * UM.Theme.getSize("default_margin").width
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.leftMargin: UM.Theme.getSize("default_margin").width

        color: UM.Theme.getColor("text")
        font: UM.Theme.getFont("large")
        text: statusText;
    }

    Rectangle{
        id: progressBar
        width: parent.width - 2 * UM.Theme.getSize("default_margin").width
        height: UM.Theme.getSize("progressbar").height
        anchors.top: statusLabel.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").height/4
        anchors.left: parent.left
        anchors.leftMargin: UM.Theme.getSize("default_margin").width
        radius: UM.Theme.getSize("progressbar_radius").width
        color: UM.Theme.getColor("progressbar_background")

        Rectangle{
            width: Math.max(parent.width * base.progress)
            height: parent.height
            color: UM.Theme.getColor("progressbar_control")
            radius: UM.Theme.getSize("progressbar_radius").width
            visible: base.backendState == 2 ? true : false
        }
    }

    Rectangle{
        id: saveRow
        width: base.width
        height: saveToButton.height
        anchors.top: progressBar.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").height
        anchors.left: parent.left

        Row {
            id: additionalComponentsRow
            anchors.top: parent.top
            anchors.right: saveToButton.visible ? saveToButton.left : parent.right
            anchors.rightMargin: UM.Theme.getSize("default_margin").width

            spacing: UM.Theme.getSize("default_margin").width
        }

        Connections {
            target: Printer
            onAdditionalComponentsChanged:
            {
                if(areaId == "saveButton") {
                    for (var component in Printer.additionalComponents["saveButton"]) {
                        Printer.additionalComponents["saveButton"][component].parent = additionalComponentsRow
                    }
                }
            }
        }

        Button {
            id: saveToButton

            tooltip: UM.OutputDeviceManager.activeDeviceDescription;
            enabled: base.backendState == 3 && base.activity == true
            height: UM.Theme.getSize("save_button_save_to_button").height

            anchors.top: parent.top
            anchors.right: deviceSelectionMenu.visible ? deviceSelectionMenu.left : parent.right
            anchors.rightMargin: deviceSelectionMenu.visible ? -3 * UM.Theme.getSize("default_lining").width : UM.Theme.getSize("default_margin").width

            text: UM.OutputDeviceManager.activeDeviceShortDescription
            onClicked:
            {
                UM.OutputDeviceManager.requestWriteToDevice(UM.OutputDeviceManager.activeDevice, PrintInformation.jobName, { "filter_by_machine": true })
            }

            style: ButtonStyle {
                background: Rectangle
                {
                    border.width: UM.Theme.getSize("default_lining").width
                    border.color: !control.enabled ? UM.Theme.getColor("action_button_disabled_border") :
                                      control.pressed ? UM.Theme.getColor("action_button_active_border") :
                                      control.hovered ? UM.Theme.getColor("action_button_hovered_border") : UM.Theme.getColor("action_button_border")
                    color: !control.enabled ? UM.Theme.getColor("action_button_disabled") :
                               control.pressed ? UM.Theme.getColor("action_button_active") :
                               control.hovered ? UM.Theme.getColor("action_button_hovered") : UM.Theme.getColor("action_button")
                    Behavior on color { ColorAnimation { duration: 50; } }

                    implicitWidth: actualLabel.contentWidth + (UM.Theme.getSize("default_margin").width * 2)

                    Label {
                        id: actualLabel
                        anchors.centerIn: parent
                        color: !control.enabled ? UM.Theme.getColor("action_button_disabled_text") :
                                   control.pressed ? UM.Theme.getColor("action_button_active_text") :
                                   control.hovered ? UM.Theme.getColor("action_button_hovered_text") : UM.Theme.getColor("action_button_text")
                        font: UM.Theme.getFont("action_button")
                        text: control.text;
                    }
                }
                label: Item { }
            }
        }

        Button {
            id: deviceSelectionMenu
            tooltip: catalog.i18nc("@info:tooltip","Select the active output device");
            anchors.top: parent.top
            anchors.right: parent.right

            anchors.rightMargin: UM.Theme.getSize("default_margin").width
            width: UM.Theme.getSize("save_button_save_to_button").height
            height: UM.Theme.getSize("save_button_save_to_button").height
            enabled: base.backendState == 3 && base.activity == true
            visible: devicesModel.deviceCount > 1


            style: ButtonStyle {
                background: Rectangle {
                    id: deviceSelectionIcon
                    border.width: UM.Theme.getSize("default_lining").width
                    border.color: !control.enabled ? UM.Theme.getColor("action_button_disabled_border") :
                                      control.pressed ? UM.Theme.getColor("action_button_active_border") :
                                      control.hovered ? UM.Theme.getColor("action_button_hovered_border") : UM.Theme.getColor("action_button_border")
                    color: !control.enabled ? UM.Theme.getColor("action_button_disabled") :
                               control.pressed ? UM.Theme.getColor("action_button_active") :
                               control.hovered ? UM.Theme.getColor("action_button_hovered") : UM.Theme.getColor("action_button")
                    Behavior on color { ColorAnimation { duration: 50; } }
                    anchors.left: parent.left
                    anchors.leftMargin: UM.Theme.getSize("save_button_text_margin").width / 2;
                    width: parent.height
                    height: parent.height

                    UM.RecolorImage {
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.horizontalCenter: parent.horizontalCenter
                        width: UM.Theme.getSize("standard_arrow").width
                        height: UM.Theme.getSize("standard_arrow").height
                        sourceSize.width: width
                        sourceSize.height: height
                        color: !control.enabled ? UM.Theme.getColor("action_button_disabled_text") :
                                   control.pressed ? UM.Theme.getColor("action_button_active_text") :
                                   control.hovered ? UM.Theme.getColor("action_button_hovered_text") : UM.Theme.getColor("action_button_text");
                        source: UM.Theme.getIcon("arrow_bottom");
                    }
                }
                label: Label{ }
            }

            menu: Menu {
                id: devicesMenu;
                Instantiator {
                    model: devicesModel;
                    MenuItem {
                        text: model.description
                        checkable: true;
                        checked: model.id == UM.OutputDeviceManager.activeDevice;
                        exclusiveGroup: devicesMenuGroup;
                        onTriggered: {
                            UM.OutputDeviceManager.setActiveDevice(model.id);
                        }
                    }
                    onObjectAdded: devicesMenu.insertItem(index, object)
                    onObjectRemoved: devicesMenu.removeItem(object)
                }
                ExclusiveGroup { id: devicesMenuGroup; }
            }
        }
        UM.OutputDevicesModel { id: devicesModel; }
    }
}
