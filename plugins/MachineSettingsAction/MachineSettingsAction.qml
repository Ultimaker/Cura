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
    id: base
    property var extrudersModel: Cura.ExtrudersModel{}

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

        TabView
        {
            id: settingsTabs
            height: parent.height - y
            width: parent.width
            anchors.left: parent.left
            anchors.top: pageTitle.bottom
            anchors.topMargin: UM.Theme.getSize("default_margin").height

            property real columnWidth: Math.floor((width - 3 * UM.Theme.getSize("default_margin").width) / 2)

            Tab
            {
                title: catalog.i18nc("@title:tab", "Printer");
                anchors.margins: UM.Theme.getSize("default_margin").width

                Column
                {
                    spacing: UM.Theme.getSize("default_margin").height

                    Row
                    {
                        width: parent.width
                        spacing: UM.Theme.getSize("default_margin").height

                        Column
                        {
                            width: settingsTabs.columnWidth
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
                                rowSpacing: UM.Theme.getSize("default_lining").width

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
                            width: settingsTabs.columnWidth
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
                                rowSpacing: UM.Theme.getSize("default_lining").width

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
                                    text: catalog.i18nc("@label", "Number of Extruders")
                                    visible: extruderCountComboBox.visible
                                }

                                ComboBox
                                {
                                    id: extruderCountComboBox
                                    visible: manager.definedExtruderCount > 1
                                    model: ListModel
                                    {
                                        id: extruderCountModel
                                        Component.onCompleted:
                                        {
                                            for(var i = 0; i < manager.definedExtruderCount; i++)
                                            {
                                                extruderCountModel.append({text: String(i + 1), value: i});
                                            }
                                        }
                                    }
                                    currentIndex: machineExtruderCountProvider.properties.value - 1
                                    onActivated:
                                    {
                                        machineExtruderCountProvider.setPropertyValue("value", index + 1);
                                        manager.forceUpdate();
                                        if(index > 0)
                                        {
                                            // multiextrusion; make sure one of these extruder stacks is active
                                            if(ExtruderManager.activeExtruderIndex == -1)
                                            {
                                                ExtruderManager.setActiveExtruderIndex(0);
                                            }
                                            else if(ExtruderManager.activeExtruderIndex > index)
                                            {
                                                ExtruderManager.setActiveExtruderIndex(index);
                                            }
                                        }
                                        else
                                        {
                                            // single extrusion; make sure the machine stack is active
                                            if(ExtruderManager.activeExtruderIndex != -1)
                                            {
                                                ExtruderManager.setActiveExtruderIndex(-1);
                                            }
                                        }
                                    }
                                }
                                Item { width: UM.Theme.getSize("default_margin").width; height: UM.Theme.getSize("default_margin").height; visible: extruderCountComboBox.visible }


                                Label
                                {
                                    text: catalog.i18nc("@label", "Nozzle size")
                                    visible: nozzleSizeField.visible
                                }
                                TextField
                                {
                                    id: nozzleSizeField
                                    text: machineNozzleSizeProvider.properties.value
                                    visible: !Cura.MachineManager.hasVariants && machineExtruderCountProvider.properties.value == 1
                                    validator: RegExpValidator { regExp: /[0-9\.]{0,6}/ }
                                    onEditingFinished: { machineNozzleSizeProvider.setPropertyValue("value", text) }
                                }
                                Label
                                {
                                    text: catalog.i18nc("@label", "mm")
                                    visible: nozzleSizeField.visible
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
                            width: settingsTabs.columnWidth
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
                            width: settingsTabs.columnWidth
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

            onCurrentIndexChanged:
            {
                if(currentIndex > 0)
                {
                    ExtruderManager.setActiveExtruderIndex(currentIndex - 1);
                }
            }

            Repeater
            {
                model: (machineExtruderCountProvider.properties.value > 1) ? parseInt(machineExtruderCountProvider.properties.value) : 0

                Tab
                {
                    title: base.extrudersModel.getItem(index).name
                    anchors.margins: UM.Theme.getSize("default_margin").width

                    Column
                    {
                        spacing: UM.Theme.getSize("default_margin").width

                        Label
                        {
                            text: catalog.i18nc("@label", "Printer Settings")
                            font.bold: true
                        }

                        Grid
                        {
                            columns: 3
                            columnSpacing: UM.Theme.getSize("default_margin").width
                            rowSpacing: UM.Theme.getSize("default_lining").width

                            Label
                            {
                                text: catalog.i18nc("@label", "Nozzle size")
                            }
                            TextField
                            {
                                id: extruderNozzleSizeField
                                text: extruderNozzleSizeProvider.properties.value
                                validator: RegExpValidator { regExp: /[0-9\.]{0,6}/ }
                                onEditingFinished: { extruderNozzleSizeProvider.setPropertyValue("value", text) }
                            }
                            Label
                            {
                                text: catalog.i18nc("@label", "mm")
                            }

                            Label
                            {
                                text: catalog.i18nc("@label", "Nozzle offset X")
                            }
                            TextField
                            {
                                id: extruderOffsetXField
                                text: extruderOffsetXProvider.properties.value
                                validator: RegExpValidator { regExp: /[0-9\.]{0,6}/ }
                                onEditingFinished: { extruderOffsetXProvider.setPropertyValue("value", text) }
                            }
                            Label
                            {
                                text: catalog.i18nc("@label", "mm")
                            }
                            Label
                            {
                                text: catalog.i18nc("@label", "Nozzle offset Y")
                            }
                            TextField
                            {
                                id: extruderOffsetYField
                                text: extruderOffsetYProvider.properties.value
                                validator: RegExpValidator { regExp: /[0-9\.]{0,6}/ }
                                onEditingFinished: { extruderOffsetYProvider.setPropertyValue("value", text) }
                            }
                            Label
                            {
                                text: catalog.i18nc("@label", "mm")
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
                                width: settingsTabs.columnWidth
                                Label
                                {
                                    text: catalog.i18nc("@label", "Extruder Start Gcode")
                                }
                                TextArea
                                {
                                    id: extruderStartGcodeField
                                    width: parent.width
                                    height: parent.height - y
                                    font: UM.Theme.getFont("fixed")
                                    wrapMode: TextEdit.NoWrap
                                    text: extruderStartGcodeProvider.properties.value
                                    onActiveFocusChanged:
                                    {
                                        if(!activeFocus)
                                        {
                                            extruderStartGcodeProvider.setPropertyValue("value", extruderStartGcodeField.text)
                                        }
                                    }
                                }
                            }
                            Column {
                                height: parent.height
                                width: settingsTabs.columnWidth
                                Label
                                {
                                    text: catalog.i18nc("@label", "Extruder End Gcode")
                                }
                                TextArea
                                {
                                    id: extruderEndGcodeField
                                    width: parent.width
                                    height: parent.height - y
                                    font: UM.Theme.getFont("fixed")
                                    wrapMode: TextEdit.NoWrap
                                    text: extruderEndGcodeProvider.properties.value
                                    onActiveFocusChanged:
                                    {
                                        if(!activeFocus)
                                        {
                                            extruderEndGcodeProvider.setPropertyValue("value", extruderEndGcodeField.text)
                                        }
                                    }
                                }
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
        id: machineExtruderCountProvider

        containerStackId: Cura.MachineManager.activeMachineId
        key: "machine_extruder_count"
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

    UM.SettingPropertyProvider
    {
        id: extruderNozzleSizeProvider

        containerStackId: Cura.MachineManager.activeStackId
        key: "machine_nozzle_size"
        watchedProperties: [ "value" ]
        storeIndex: manager.containerIndex
    }

    UM.SettingPropertyProvider
    {
        id: extruderOffsetXProvider

        containerStackId: Cura.MachineManager.activeStackId
        key: "machine_nozzle_offset_x"
        watchedProperties: [ "value" ]
        storeIndex: manager.containerIndex
    }

    UM.SettingPropertyProvider
    {
        id: extruderOffsetYProvider

        containerStackId: Cura.MachineManager.activeStackId
        key: "machine_nozzle_offset_y"
        watchedProperties: [ "value" ]
        storeIndex: manager.containerIndex
    }

    UM.SettingPropertyProvider
    {
        id: extruderStartGcodeProvider

        containerStackId: Cura.MachineManager.activeStackId
        key: "machine_extruder_start_code"
        watchedProperties: [ "value" ]
        storeIndex: manager.containerIndex
    }

    UM.SettingPropertyProvider
    {
        id: extruderEndGcodeProvider

        containerStackId: Cura.MachineManager.activeStackId
        key: "machine_extruder_end_code"
        watchedProperties: [ "value" ]
        storeIndex: manager.containerIndex
    }


}