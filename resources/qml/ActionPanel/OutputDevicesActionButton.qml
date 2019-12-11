// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.1
import QtQuick.Layouts 1.3

import UM 1.1 as UM
import Cura 1.0 as Cura

Item
{
    id: widget

    function requestWriteToDevice()
    {
        UM.OutputDeviceManager.requestWriteToDevice(UM.OutputDeviceManager.activeDevice, PrintInformation.jobName,
            { "filter_by_machine": true, "preferred_mimetypes": Cura.MachineManager.activeMachine.preferred_output_file_formats });
    }

    Cura.PrimaryButton
    {
        id: saveToButton
        height: parent.height
        fixedWidthMode: true
        cornerSide: deviceSelectionMenu.visible ? Cura.RoundedRectangle.Direction.Left : Cura.RoundedRectangle.Direction.All

        anchors
        {
            top: parent.top
            left: parent.left
            right: deviceSelectionMenu.visible ? deviceSelectionMenu.left : parent.right
        }

        tooltip: UM.OutputDeviceManager.activeDeviceDescription

        text: UM.OutputDeviceManager.activeDeviceShortDescription

        onClicked:
        {
            forceActiveFocus()
            widget.requestWriteToDevice()
        }
    }

    Cura.ActionButton
    {
        id: deviceSelectionMenu
        height: parent.height

        shadowEnabled: true
        shadowColor: UM.Theme.getColor("primary_shadow")
        cornerSide: Cura.RoundedRectangle.Direction.Right

        anchors
        {
            top: parent.top
            right: parent.right
        }

        leftPadding: UM.Theme.getSize("narrow_margin").width //Need more space than usual here for wide text.
        rightPadding: UM.Theme.getSize("narrow_margin").width
        iconSource: popup.opened ? UM.Theme.getIcon("arrow_top") : UM.Theme.getIcon("arrow_bottom")
        color: UM.Theme.getColor("action_panel_secondary")
        visible: (devicesModel.deviceCount > 1)

        onClicked: popup.opened ? popup.close() : popup.open()

        Popup
        {
            id: popup
            padding: 0

            y: -height
            x: parent.width - width

            closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutsideParent

            contentItem: ColumnLayout
            {
                Repeater
                {
                    model: devicesModel

                    delegate: Cura.ActionButton
                    {
                        text: model.description
                        visible: model.id != UM.OutputDeviceManager.activeDevice  // Don't show the active device in the list
                        color: "transparent"
                        cornerRadius: 0
                        hoverColor: UM.Theme.getColor("primary")
                        Layout.fillWidth: true
                        // The total width of the popup should be defined by the largest button. By stating that each
                        // button should be minimally the size of it's content (aka; implicitWidth) we can ensure that.
                        Layout.minimumWidth: implicitWidth
                        Layout.preferredHeight: widget.height
                        onClicked:
                        {
                            UM.OutputDeviceManager.setActiveDevice(model.id)
                            popup.close()
                        }
                    }
                }
            }

            background: Rectangle
            {
                opacity: visible ? 1 : 0
                Behavior on opacity { NumberAnimation { duration: 100 } }
                color: UM.Theme.getColor("action_panel_secondary")
            }
        }
    }

    UM.OutputDevicesModel { id: devicesModel }
}