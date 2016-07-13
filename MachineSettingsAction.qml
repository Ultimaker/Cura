// Copyright (c) 2016 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1
import QtQuick.Window 2.1

import UM 1.2 as UM
import Cura 1.0 as Cura


Cura.MachineAction
{
    anchors.fill: parent;
    Item
    {
        id: bedLevelMachineAction
        anchors.fill: parent;

        UM.I18nCatalog { id: catalog; name: "cura"; }

        Label
        {
            id: pageTitle
            width: parent.width
            text: catalog.i18nc("@title", "Machine Settings")
            wrapMode: Text.WordWrap
            font.pointSize: 18;
        }
        Label
        {
            id: pageDescription
            anchors.top: pageTitle.bottom
            anchors.topMargin: UM.Theme.getSize("default_margin").height
            width: parent.width
            wrapMode: Text.WordWrap
            text: catalog.i18nc("@label", "Please enter the correct settings for your printer below:")
        }

        Column
        {
            id: pageCheckboxes
            height: childrenRect.height
            anchors.left: parent.left
            anchors.top: pageDescription.bottom
            anchors.topMargin: UM.Theme.getSize("default_margin").height
            width: parent.width - UM.Theme.getSize("default_margin").width
            spacing: UM.Theme.getSize("default_margin").height

            Grid
            {
                columns: 3
                columnSpacing: UM.Theme.getSize("default_margin").width

                Label
                {
                    text: catalog.i18nc("@label","X (Width)")
                }
                TextField
                {
                    id: buildAreaWidthField
                    text: machineWidthProvider.properties.value
                    validator: RegExpValidator { regExp: /[0-9]{0,6}/ }
                    onEditingFinished: { machineWidthProvider.setPropertyValue("value", text); manager.forceUpdate() }
                }
                Label
                {
                    text: catalog.i18nc("@label","mm")
                }

                Label
                {
                    text: catalog.i18nc("@label","Y (Depth)")
                }
                TextField
                {
                    id: buildAreaDepthField
                    text: machineDepthProvider.properties.value
                    validator: RegExpValidator { regExp: /[0-9]{0,6}/ }
                    onEditingFinished: { machineDepthProvider.setPropertyValue("value", text); manager.forceUpdate() }
                }
                Label
                {
                    text: catalog.i18nc("@label","mm")
                }

                Label
                {
                    text: catalog.i18nc("@label","Z (Height)")
                }
                TextField
                {
                    id: buildAreaHeightField
                    text: machineHeightProvider.properties.value
                    validator: RegExpValidator { regExp: /[0-9]{0,6}/ }
                    onEditingFinished: { machineHeightProvider.setPropertyValue("value", text); manager.forceUpdate() }
                }
                Label
                {
                    text: catalog.i18nc("@label","mm")
                }

                Item
                {
                    width: UM.Theme.getSize("default_margin").width
                    height: UM.Theme.getSize("default_margin").height
                }
                Item
                {
                    width: UM.Theme.getSize("default_margin").width
                    height: UM.Theme.getSize("default_margin").height
                }
                Item
                {
                    width: UM.Theme.getSize("default_margin").width
                    height: UM.Theme.getSize("default_margin").height
                }

                Label
                {
                    text: catalog.i18nc("@label","Nozzle size")
                }
                TextField
                {
                    id: nozzleSizeField
                    text: machineNozzleSizeProvider.properties.value
                    validator: RegExpValidator { regExp: /[0-9\.]{0,6}/ }
                    onEditingFinished: { machineNozzleSizeProvider.setPropertyValue("value", text) }
                }
                Label
                {
                    text: catalog.i18nc("@label","mm")
                }
            }

            Column
            {
                CheckBox
                {
                    id: heatedBedCheckBox
                    text: catalog.i18nc("@option:check","Heated Bed")
                    checked: String(machineHeatedBedProvider.properties.value).toLowerCase() != 'false'
                    onClicked: machineHeatedBedProvider.setPropertyValue("value", checked)
                }
                CheckBox
                {
                    id: centerIsZeroCheckBox
                    text: catalog.i18nc("@option:check","Machine Center is Zero")
                    checked: String(machineCenterIsZeroProvider.properties.value).toLowerCase() != 'false'
                    onClicked: machineCenterIsZeroProvider.setPropertyValue("value", checked)
                }
            }

            Row
            {
                spacing: UM.Theme.getSize("default_margin").width
                anchors.left: parent.left
                anchors.right: parent.right
                Column
                {
                    width: parent.width / 2
                    Label
                    {
                        text: catalog.i18nc("@label","Start Gcode")
                    }
                    TextArea
                    {
                        id: machineStartGcodeField
                        width: parent.width
                        text: machineStartGcodeProvider.properties.value
                        onActiveFocusChanged:
                        {
                            if(!activeFocus)
                            {
                                machineStartGcodeProvider.setPropertyValue("value", machineStartGcodeField.text)
                            }
                        }
                    }
                }
                Column{
                    width: parent.width / 2
                    Label
                    {
                        text: catalog.i18nc("@label","End Gcode")
                    }
                    TextArea
                    {
                        id: machineEndGcodeField
                        width: parent.width
                        text: machineEndGcodeProvider.properties.value
                        onActiveFocusChanged:
                        {
                            if(!activeFocus)
                            {
                                machineEndGcodeProvider.setPropertyValue("value", machineEndGcodeField.text)
                            }
                        }
                    }
                }
            }
        }
    }

    UM.SettingPropertyProvider
    {
        id: machineWidthProvider

        containerStackId: Cura.MachineManager.activeMachineId
        key: "machine_width"
        watchedProperties: [ "value" ]
        storeIndex: 0
    }

    UM.SettingPropertyProvider
    {
        id: machineDepthProvider

        containerStackId: Cura.MachineManager.activeMachineId
        key: "machine_depth"
        watchedProperties: [ "value" ]
        storeIndex: 0
    }

    UM.SettingPropertyProvider
    {
        id: machineHeightProvider

        containerStackId: Cura.MachineManager.activeMachineId
        key: "machine_height"
        watchedProperties: [ "value" ]
        storeIndex: 0
    }

    UM.SettingPropertyProvider
    {
        id: machineNozzleSizeProvider

        containerStackId: Cura.MachineManager.activeMachineId
        key: "machine_nozzle_size"
        watchedProperties: [ "value" ]
        storeIndex: 0
    }

    UM.SettingPropertyProvider
    {
        id: machineHeatedBedProvider

        containerStackId: Cura.MachineManager.activeMachineId
        key: "machine_heated_bed"
        watchedProperties: [ "value" ]
        storeIndex: 0
    }

    UM.SettingPropertyProvider
    {
        id: machineCenterIsZeroProvider

        containerStackId: Cura.MachineManager.activeMachineId
        key: "machine_center_is_zero"
        watchedProperties: [ "value" ]
        storeIndex: 0
    }


    UM.SettingPropertyProvider
    {
        id: machineStartGcodeProvider

        containerStackId: Cura.MachineManager.activeMachineId
        key: "machine_start_gcode"
        watchedProperties: [ "value" ]
        storeIndex: 0
    }

    UM.SettingPropertyProvider
    {
        id: machineEndGcodeProvider

        containerStackId: Cura.MachineManager.activeMachineId
        key: "machine_end_gcode"
        watchedProperties: [ "value" ]
        storeIndex: 0
    }

}