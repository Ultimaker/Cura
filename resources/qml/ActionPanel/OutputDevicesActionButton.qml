// Copyright (c) 2021 Ultimaker B.V.
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

    Cura.PrimaryButton
    {
        id: deviceSelectionMenu
        height: parent.height

        anchors
        {
            top: parent.top
            right: parent.right
        }

        leftPadding: UM.Theme.getSize("narrow_margin").width //Need more space than usual here for wide text.
        rightPadding: UM.Theme.getSize("narrow_margin").width
        iconSource: popup.opened ? UM.Theme.getIcon("ChevronSingleUp") : UM.Theme.getIcon("ChevronSingleDown")
        color: popup.opened ? hoverColor : UM.Theme.getColor("action_panel_secondary")
        visible: (devicesModel.deviceCount > 1)

        onClicked: popup.opened ? popup.close() : popup.open()

        Popup
        {
            id: popup
            padding: 0
            spacing: 0

            y: -height
            x: parent.width - width

            closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutsideParent

            contentItem: ColumnLayout
            {
                spacing: 0

                Repeater
                {
                    model: devicesModel

                    delegate: Cura.PrimaryButton
                    {
                        text: model.description
                        visible: model.id != UM.OutputDeviceManager.activeDevice  // Don't show the active device in the list
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
        }
    }

    UM.OutputDevicesModel { id: devicesModel }
}
