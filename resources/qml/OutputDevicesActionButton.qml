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

    Cura.ActionButton
    {
        id: saveToButton
        height: parent.height

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
            forceActiveFocus();
            UM.OutputDeviceManager.requestWriteToDevice(UM.OutputDeviceManager.activeDevice, PrintInformation.jobName,
                { "filter_by_machine": true, "preferred_mimetypes": Cura.MachineManager.activeMachine.preferred_output_file_formats });
        }
    }

    Cura.ActionButton
    {
        id: deviceSelectionMenu
        height: parent.height

        anchors
        {
            top: parent.top
            right: parent.right
        }

        tooltip: catalog.i18nc("@info:tooltip", "Select the active output device")
        iconSource: popup.opened ? UM.Theme.getIcon("arrow_top") : UM.Theme.getIcon("arrow_bottom")
        visible: (devicesModel.deviceCount > 1)

        onClicked: popup.opened ? popup.close() : popup.open()

        Popup
        {
            id: popup

            y: -height
            x: parent.width - width

            closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutsideParent

            contentItem: Column
            {
                Repeater
                {
                    model: devicesModel

                    delegate: Cura.ActionButton
                    {
                        text: model.description
                        color: "transparent"
                        hoverColor: "red"

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
                color: UM.Theme.getColor("primary")
                border.color: UM.Theme.getColor("lining")
                border.width: UM.Theme.getSize("default_lining").width
            }
        }
    }

    UM.OutputDevicesModel { id: devicesModel }
}