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
                            validator: RegExpValidator { regExp: /[0-9\.]{0,6}/ }
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
                            validator: RegExpValidator { regExp: /[0-9\.]{0,6}/ }
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
                            validator: RegExpValidator { regExp: /[0-9\.]{0,6}/ }
                            onEditingFinished: { machineHeightProvider.setPropertyValue("value", text); manager.forceUpdate() }
                        }
                        Label
                        {
                            text: catalog.i18nc("@label", "mm")
                        }
                    }

                    Column
                    {
                        Row
                        {
                            spacing: UM.Theme.getSize("default_margin").width

                            Label
                            {
                                text: catalog.i18nc("@label", "Build Plate Shape")
                            }

                            ComboBox
                            {
                                id: shapeComboBox
                                model: ListModel
                                {
                                    id: shapesModel
                                    Component.onCompleted:
                                    {
                                        // Options come in as a string-representation of an OrderedDict
                                        var options = machineShapeProvider.properties.options.match(/^OrderedDict\(\[\((.*)\)\]\)$/);
                                        if(options)
                                        {
                                            options = options[1].split("), (")
                                            for(var i = 0; i < options.length; i++)
                                            {
                                                var option = options[i].substring(1, options[i].length - 1).split("', '")
                                                shapesModel.append({text: option[1], value: option[0]});
                                            }
                                        }
                                    }
                                }
                                currentIndex:
                                {
                                    var currentValue = machineShapeProvider.properties.value;
                                    var index = 0;
                                    for(var i = 0; i < shapesModel.count; i++)
                                    {
                                        if(shapesModel.get(i).value == currentValue) {
                                            index = i;
                                            break;
                                        }
                                    }
                                    return index
                                }
                                onActivated:
                                {
                                    machineShapeProvider.setPropertyValue("value", shapesModel.get(index).value);
                                    manager.forceUpdate();
                                }
                            }
                        }
                        CheckBox
                        {
                            id: centerIsZeroCheckBox
                            text: catalog.i18nc("@option:check", "Machine Center is Zero")
                            checked: String(machineCenterIsZeroProvider.properties.value).toLowerCase() != 'false'
                            onClicked:
                            {
                                    machineCenterIsZeroProvider.setPropertyValue("value", checked);
                                    manager.forceUpdate();
                            }
                        }
                        CheckBox
                        {
                            id: heatedBedCheckBox
                            text: catalog.i18nc("@option:check", "Heated Bed")
                            checked: String(machineHeatedBedProvider.properties.value).toLowerCase() != 'false'
                            onClicked: machineHeatedBedProvider.setPropertyValue("value", checked)
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
                            model: ListModel
                            {
                                id: flavorModel
                                Component.onCompleted:
                                {
                                    // Options come in as a string-representation of an OrderedDict
                                    var options = machineGCodeFlavorProvider.properties.options.match(/^OrderedDict\(\[\((.*)\)\]\)$/);
                                    if(options)
                                    {
                                        options = options[1].split("), (")
                                        for(var i = 0; i < options.length; i++)
                                        {
                                            var option = options[i].substring(1, options[i].length - 1).split("', '")
                                            flavorModel.append({text: option[1], value: option[0]});
                                        }
                                    }
                                }
                            }
                            currentIndex:
                            {
                                var currentValue = machineGCodeFlavorProvider.properties.value;
                                var index = 0;
                                for(var i = 0; i < flavorModel.count; i++)
                                {
                                    if(flavorModel.get(i).value == currentValue) {
                                        index = i;
                                        break;
                                    }
                                }
                                return index
                            }
                            onActivated:
                            {
                                machineGCodeFlavorProvider.setPropertyValue("value", flavorModel.get(index).value);
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
                            validator: RegExpValidator { regExp: /[0-9\.]{0,6}/ }
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
                            validator: RegExpValidator { regExp: /[0-9\.]{0,6}/ }
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
                            validator: RegExpValidator { regExp: /[0-9\.]{0,6}/ }
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
                            validator: RegExpValidator { regExp: /[0-9\.]{0,6}/ }
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
                            visible: !Cura.MachineManager.hasVariants
                        }
                        TextField
                        {
                            id: nozzleSizeField
                            text: machineNozzleSizeProvider.properties.value
                            visible: !Cura.MachineManager.hasVariants
                            validator: RegExpValidator { regExp: /[0-9\.]{0,6}/ }
                            onEditingFinished: { machineNozzleSizeProvider.setPropertyValue("value", text) }
                        }
                        Label
                        {
                            text: catalog.i18nc("@label", "mm")
                            visible: !Cura.MachineManager.hasVariants
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
                        font: UM.Theme.getFont("fixed")
                        wrapMode: TextEdit.NoWrap
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
                        font: UM.Theme.getFont("fixed")
                        wrapMode: TextEdit.NoWrap
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
        storeIndex: manager.containerIndex
    }

    UM.SettingPropertyProvider
    {
        id: machineDepthProvider

        containerStackId: Cura.MachineManager.activeMachineId
        key: "machine_depth"
        watchedProperties: [ "value" ]
        storeIndex: manager.containerIndex
    }

    UM.SettingPropertyProvider
    {
        id: machineHeightProvider

        containerStackId: Cura.MachineManager.activeMachineId
        key: "machine_height"
        watchedProperties: [ "value" ]
        storeIndex: manager.containerIndex
    }

    UM.SettingPropertyProvider
    {
        id: machineShapeProvider

        containerStackId: Cura.MachineManager.activeMachineId
        key: "machine_shape"
        watchedProperties: [ "value", "options" ]
        storeIndex: manager.containerIndex
    }

    UM.SettingPropertyProvider
    {
        id: machineHeatedBedProvider

        containerStackId: Cura.MachineManager.activeMachineId
        key: "machine_heated_bed"
        watchedProperties: [ "value" ]
        storeIndex: manager.containerIndex
    }

    UM.SettingPropertyProvider
    {
        id: machineCenterIsZeroProvider

        containerStackId: Cura.MachineManager.activeMachineId
        key: "machine_center_is_zero"
        watchedProperties: [ "value" ]
        storeIndex: manager.containerIndex
    }

    UM.SettingPropertyProvider
    {
        id: machineGCodeFlavorProvider

        containerStackId: Cura.MachineManager.activeMachineId
        key: "machine_gcode_flavor"
        watchedProperties: [ "value", "options" ]
        storeIndex: manager.containerIndex
    }

    UM.SettingPropertyProvider
    {
        id: machineNozzleSizeProvider

        containerStackId: Cura.MachineManager.activeMachineId
        key: "machine_nozzle_size"
        watchedProperties: [ "value" ]
        storeIndex: manager.containerIndex
    }

    UM.SettingPropertyProvider
    {
        id: gantryHeightProvider

        containerStackId: Cura.MachineManager.activeMachineId
        key: "gantry_height"
        watchedProperties: [ "value" ]
        storeIndex: manager.containerIndex
    }

    UM.SettingPropertyProvider
    {
        id: machineHeadPolygonProvider

        containerStackId: Cura.MachineManager.activeMachineId
        key: "machine_head_with_fans_polygon"
        watchedProperties: [ "value" ]
        storeIndex: manager.containerIndex
    }


    UM.SettingPropertyProvider
    {
        id: machineStartGcodeProvider

        containerStackId: Cura.MachineManager.activeMachineId
        key: "machine_start_gcode"
        watchedProperties: [ "value" ]
        storeIndex: manager.containerIndex
    }

    UM.SettingPropertyProvider
    {
        id: machineEndGcodeProvider

        containerStackId: Cura.MachineManager.activeMachineId
        key: "machine_end_gcode"
        watchedProperties: [ "value" ]
        storeIndex: manager.containerIndex
    }

}