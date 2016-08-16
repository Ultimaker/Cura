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
            height: parent.height - y
            width: parent.width - UM.Theme.getSize("default_margin").width
            spacing: UM.Theme.getSize("default_margin").height

            anchors.left: parent.left
            anchors.top: pageDescription.bottom
            anchors.topMargin: UM.Theme.getSize("default_margin").height

            Row
            {
                width: parent.width
                spacing: UM.Theme.getSize("default_margin").height

                Column
                {
                    width: parent.width / 2
                    spacing: UM.Theme.getSize("default_margin").height

                    Label
                    {
                        text: catalog.i18nc("@label", "Printer Settings")
                        font.bold: true
                    }

                    Grid
                    {
                        columns: 3
                        columnSpacing: UM.Theme.getSize("default_margin").width

                        Label
                        {
                            text: catalog.i18nc("@label", "X (Width)")
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
                            text: catalog.i18nc("@label", "mm")
                        }

                        Label
                        {
                            text: catalog.i18nc("@label", "Y (Depth)")
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
                            text: catalog.i18nc("@label", "mm")
                        }

                        Label
                        {
                            text: catalog.i18nc("@label", "Z (Height)")
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
                            text: catalog.i18nc("@label", "mm")
                        }
                    }

                    Column
                    {
                        CheckBox
                        {
                            id: heatedBedCheckBox
                            text: catalog.i18nc("@option:check", "Heated Bed")
                            checked: String(machineHeatedBedProvider.properties.value).toLowerCase() != 'false'
                            onClicked: machineHeatedBedProvider.setPropertyValue("value", checked)
                        }
                        CheckBox
                        {
                            id: centerIsZeroCheckBox
                            text: catalog.i18nc("@option:check", "Machine Center is Zero")
                            checked: String(machineCenterIsZeroProvider.properties.value).toLowerCase() != 'false'
                            onClicked: machineCenterIsZeroProvider.setPropertyValue("value", checked)
                        }
                    }

                    Row
                    {
                        spacing: UM.Theme.getSize("default_margin").width

                        Label
                        {
                            text: catalog.i18nc("@label", "GCode Flavor")
                        }

                        ComboBox
                        {
                            model: ["RepRap (Marlin/Sprinter)", "UltiGCode"]
                            currentIndex: machineGCodeFlavorProvider.properties.value != model[1] ? 0 : 1
                            onActivated:
                            {
                                machineGCodeFlavorProvider.setPropertyValue("value", model[index]);
                                manager.updateHasMaterialsMetadata();
                            }
                        }
                    }
                }

                Column
                {
                    width: parent.width / 2
                    spacing: UM.Theme.getSize("default_margin").height

                    Label
                    {
                        text: catalog.i18nc("@label", "Printhead Settings")
                        font.bold: true
                    }

                    Grid
                    {
                        columns: 3
                        columnSpacing: UM.Theme.getSize("default_margin").width

                        Label
                        {
                            text: catalog.i18nc("@label", "X min")
                        }
                        TextField
                        {
                            id: printheadXMinField
                            text: getHeadPolygonCoord("x", "min")
                            validator: RegExpValidator { regExp: /[0-9]{0,6}/ }
                            onEditingFinished: setHeadPolygon()
                        }
                        Label
                        {
                            text: catalog.i18nc("@label", "mm")
                        }

                        Label
                        {
                            text: catalog.i18nc("@label", "Y min")
                        }
                        TextField
                        {
                            id: printheadYMinField
                            text: getHeadPolygonCoord("y", "min")
                            validator: RegExpValidator { regExp: /[0-9]{0,6}/ }
                            onEditingFinished: setHeadPolygon()
                        }
                        Label
                        {
                            text: catalog.i18nc("@label", "mm")
                        }

                        Label
                        {
                            text: catalog.i18nc("@label", "X max")
                        }
                        TextField
                        {
                            id: printheadXMaxField
                            text: getHeadPolygonCoord("x", "max")
                            validator: RegExpValidator { regExp: /[0-9]{0,6}/ }
                            onEditingFinished: setHeadPolygon()
                        }
                        Label
                        {
                            text: catalog.i18nc("@label", "mm")
                        }

                        Label
                        {
                            text: catalog.i18nc("@label", "Y max")
                        }
                        TextField
                        {
                            id: printheadYMaxField
                            text: getHeadPolygonCoord("y", "max")
                            validator: RegExpValidator { regExp: /[0-9]{0,6}/ }
                            onEditingFinished: setHeadPolygon()
                        }
                        Label
                        {
                            text: catalog.i18nc("@label", "mm")
                        }

                        Item { width: UM.Theme.getSize("default_margin").width; height: UM.Theme.getSize("default_margin").height }
                        Item { width: UM.Theme.getSize("default_margin").width; height: UM.Theme.getSize("default_margin").height }
                        Item { width: UM.Theme.getSize("default_margin").width; height: UM.Theme.getSize("default_margin").height }

                        Label
                        {
                            text: catalog.i18nc("@label", "Gantry height")
                        }
                        TextField
                        {
                            id: gantryHeightField
                            text: gantryHeightProvider.properties.value
                            validator: RegExpValidator { regExp: /[0-9\.]{0,6}/ }
                            onEditingFinished: { gantryHeightProvider.setPropertyValue("value", text) }
                        }
                        Label
                        {
                            text: catalog.i18nc("@label", "mm")
                        }

                        Item { width: UM.Theme.getSize("default_margin").width; height: UM.Theme.getSize("default_margin").height }
                        Item { width: UM.Theme.getSize("default_margin").width; height: UM.Theme.getSize("default_margin").height }
                        Item { width: UM.Theme.getSize("default_margin").width; height: UM.Theme.getSize("default_margin").height }

                        Label
                        {
                            text: catalog.i18nc("@label", "Nozzle size")
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
                            text: catalog.i18nc("@label", "mm")
                        }
                    }
                }
            }

            Row
            {
                spacing: UM.Theme.getSize("default_margin").width
                anchors.left: parent.left
                anchors.right: parent.right
                height: parent.height - y
                Column
                {
                    height: parent.height
                    width: parent.width / 2
                    Label
                    {
                        text: catalog.i18nc("@label", "Start Gcode")
                    }
                    TextArea
                    {
                        id: machineStartGcodeField
                        width: parent.width
                        height: parent.height - y
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
                Column {
                    height: parent.height
                    width: parent.width / 2
                    Label
                    {
                        text: catalog.i18nc("@label", "End Gcode")
                    }
                    TextArea
                    {
                        id: machineEndGcodeField
                        width: parent.width
                        height: parent.height - y
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

    function getHeadPolygonCoord(axis, minMax)
    {
        var polygon = JSON.parse(machineHeadPolygonProvider.properties.value);
        var item = (axis == "x") ? 0 : 1
        var result = polygon[0][item];
        for(var i = 1; i < polygon.length; i++) {
            if (minMax == "min") {
                result = Math.min(result, polygon[i][item]);
            } else {
                result = Math.max(result, polygon[i][item]);
            }
        }
        return Math.abs(result);
    }

    function setHeadPolygon()
    {
        var polygon = [];
        polygon.push([-parseFloat(printheadXMinField.text), parseFloat(printheadYMaxField.text)]);
        polygon.push([-parseFloat(printheadXMinField.text),-parseFloat(printheadYMinField.text)]);
        polygon.push([ parseFloat(printheadXMaxField.text), parseFloat(printheadYMaxField.text)]);
        polygon.push([ parseFloat(printheadXMaxField.text),-parseFloat(printheadYMinField.text)]);
        machineHeadPolygonProvider.setPropertyValue("value", JSON.stringify(polygon));
        manager.forceUpdate();
    }

    UM.SettingPropertyProvider
    {
        id: machineWidthProvider

        containerStackId: Cura.MachineManager.activeMachineId
        key: "machine_width"
        watchedProperties: [ "value" ]
        storeIndex: 3
    }

    UM.SettingPropertyProvider
    {
        id: machineDepthProvider

        containerStackId: Cura.MachineManager.activeMachineId
        key: "machine_depth"
        watchedProperties: [ "value" ]
        storeIndex: 3
    }

    UM.SettingPropertyProvider
    {
        id: machineHeightProvider

        containerStackId: Cura.MachineManager.activeMachineId
        key: "machine_height"
        watchedProperties: [ "value" ]
        storeIndex: 3
    }

    UM.SettingPropertyProvider
    {
        id: machineHeatedBedProvider

        containerStackId: Cura.MachineManager.activeMachineId
        key: "machine_heated_bed"
        watchedProperties: [ "value" ]
        storeIndex: 3
    }

    UM.SettingPropertyProvider
    {
        id: machineCenterIsZeroProvider

        containerStackId: Cura.MachineManager.activeMachineId
        key: "machine_center_is_zero"
        watchedProperties: [ "value" ]
        storeIndex: 3
    }

    UM.SettingPropertyProvider
    {
        id: machineGCodeFlavorProvider

        containerStackId: Cura.MachineManager.activeMachineId
        key: "machine_gcode_flavor"
        watchedProperties: [ "value" ]
        storeIndex: 3
    }

    UM.SettingPropertyProvider
    {
        id: machineNozzleSizeProvider

        containerStackId: Cura.MachineManager.activeMachineId
        key: "machine_nozzle_size"
        watchedProperties: [ "value" ]
        storeIndex: 3
    }

    UM.SettingPropertyProvider
    {
        id: gantryHeightProvider

        containerStackId: Cura.MachineManager.activeMachineId
        key: "gantry_height"
        watchedProperties: [ "value" ]
        storeIndex: 3
    }

    UM.SettingPropertyProvider
    {
        id: machineHeadPolygonProvider

        containerStackId: Cura.MachineManager.activeMachineId
        key: "machine_head_with_fans_polygon"
        watchedProperties: [ "value" ]
        storeIndex: 3
    }


    UM.SettingPropertyProvider
    {
        id: machineStartGcodeProvider

        containerStackId: Cura.MachineManager.activeMachineId
        key: "machine_start_gcode"
        watchedProperties: [ "value" ]
        storeIndex: 3
    }

    UM.SettingPropertyProvider
    {
        id: machineEndGcodeProvider

        containerStackId: Cura.MachineManager.activeMachineId
        key: "machine_end_gcode"
        watchedProperties: [ "value" ]
        storeIndex: 3
    }

}