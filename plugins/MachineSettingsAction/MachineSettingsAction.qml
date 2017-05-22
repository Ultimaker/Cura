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
    property int extruderTabsCount: 0

    Connections
    {
        target: base.extrudersModel
        onModelChanged:
        {
            var extruderCount = base.extrudersModel.rowCount();
            base.extruderTabsCount = extruderCount > 1 ? extruderCount : 0;
        }
    }

    Connections
    {
        target: dialog ? dialog : null
        ignoreUnknownSignals: true
        // Any which way this action dialog is dismissed, make sure it is properly finished
        onNextClicked: manager.onFinishAction()
        onBackClicked: manager.onFinishAction()
        onAccepted: manager.onFinishAction()
        onRejected: manager.onFinishAction()
        onClosing: manager.onFinishAction()
    }

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
                                columns: 2
                                columnSpacing: UM.Theme.getSize("default_margin").width
                                rowSpacing: UM.Theme.getSize("default_lining").width

                                Label
                                {
                                    text: catalog.i18nc("@label", "X (Width)")
                                }
                                Loader
                                {
                                    id: buildAreaWidthField
                                    sourceComponent: numericTextFieldWithUnit
                                    property var propertyProvider: machineWidthProvider
                                    property string unit: catalog.i18nc("@label", "mm")
                                    property bool forceUpdateOnChange: true
                                }

                                Label
                                {
                                    text: catalog.i18nc("@label", "Y (Depth)")
                                }
                                Loader
                                {
                                    id: buildAreaDepthField
                                    sourceComponent: numericTextFieldWithUnit
                                    property var propertyProvider: machineDepthProvider
                                    property string unit: catalog.i18nc("@label", "mm")
                                    property bool forceUpdateOnChange: true
                                }

                                Label
                                {
                                    text: catalog.i18nc("@label", "Z (Height)")
                                }
                                Loader
                                {
                                    id: buildAreaHeightField
                                    sourceComponent: numericTextFieldWithUnit
                                    property var propertyProvider: machineHeightProvider
                                    property string unit: catalog.i18nc("@label", "mm")
                                    property bool forceUpdateOnChange: true
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
                                            if(machineShapeProvider.properties.value != shapesModel.get(index).value)
                                            {
                                                machineShapeProvider.setPropertyValue("value", shapesModel.get(index).value);
                                                manager.forceUpdate();
                                            }
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
                                columns: 2
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
                                    text: catalog.i18nc("@label", "Y max")
                                }
                                TextField
                                {
                                    id: printheadYMaxField
                                    text: getHeadPolygonCoord("y", "max")
                                    validator: RegExpValidator { regExp: /[0-9\.]{0,6}/ }
                                    onEditingFinished: setHeadPolygon()
                                }

                                Item { width: UM.Theme.getSize("default_margin").width; height: UM.Theme.getSize("default_margin").height }
                                Item { width: UM.Theme.getSize("default_margin").width; height: UM.Theme.getSize("default_margin").height }

                                Label
                                {
                                    text: catalog.i18nc("@label", "Gantry height")
                                }
                                Loader
                                {
                                    id: gantryHeightField
                                    sourceComponent: numericTextFieldWithUnit
                                    property var propertyProvider: gantryHeightProvider
                                    property string unit: catalog.i18nc("@label", "mm")
                                }

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
                                        manager.setMachineExtruderCount(index + 1);
                                    }
                                }

                                Label
                                {
                                    text: catalog.i18nc("@label", "Material Diameter")
                                }
                                Loader
                                {
                                    id: materialDiameterField
                                    sourceComponent: numericTextFieldWithUnit
                                    property var propertyProvider: materialDiameterProvider
                                    property string unit: catalog.i18nc("@label", "mm")
                                }
                                Label
                                {
                                    text: catalog.i18nc("@label", "Nozzle size")
                                    visible: nozzleSizeField.visible
                                }
                                Loader
                                {
                                    id: nozzleSizeField
                                    visible: !Cura.MachineManager.hasVariants && machineExtruderCountProvider.properties.value == 1
                                    sourceComponent: numericTextFieldWithUnit
                                    property var propertyProvider: machineNozzleSizeProvider
                                    property string unit: catalog.i18nc("@label", "mm")
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
                                font.bold: true
                            }
                            TextArea
                            {
                                id: machineStartGcodeField
                                width: parent.width
                                height: parent.height - y
                                font: UM.Theme.getFont("fixed")
                                text: machineStartGcodeProvider.properties.value
                                onActiveFocusChanged:
                                {
                                    if(!activeFocus)
                                    {
                                        machineStartGcodeProvider.setPropertyValue("value", machineStartGcodeField.text)
                                    }
                                }
                                Component.onCompleted:
                                {
                                    wrapMode = TextEdit.NoWrap;
                                }
                            }
                        }

                        Column {
                            height: parent.height
                            width: settingsTabs.columnWidth
                            Label
                            {
                                text: catalog.i18nc("@label", "End Gcode")
                                font.bold: true
                            }
                            TextArea
                            {
                                id: machineEndGcodeField
                                width: parent.width
                                height: parent.height - y
                                font: UM.Theme.getFont("fixed")
                                text: machineEndGcodeProvider.properties.value
                                onActiveFocusChanged:
                                {
                                    if(!activeFocus)
                                    {
                                        machineEndGcodeProvider.setPropertyValue("value", machineEndGcodeField.text)
                                    }
                                }
                                Component.onCompleted:
                                {
                                    wrapMode = TextEdit.NoWrap;
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
                        var polygon_string = JSON.stringify(polygon);
                        if(polygon != machineHeadPolygonProvider.properties.value)
                        {
                            machineHeadPolygonProvider.setPropertyValue("value", polygon_string);
                            manager.forceUpdate();
                        }
                    }
                }
            }

            onCurrentIndexChanged:
            {
                if(currentIndex > 0)
                {
                    contentItem.forceActiveFocus();
                    ExtruderManager.setActiveExtruderIndex(currentIndex - 1);
                }
            }

            Repeater
            {
                id: extruderTabsRepeater
                model: base.extruderTabsCount

                Tab
                {
                    title: base.extrudersModel.getItem(index).name
                    anchors.margins: UM.Theme.getSize("default_margin").width

                    Column
                    {
                        spacing: UM.Theme.getSize("default_margin").width

                        Label
                        {
                            text: catalog.i18nc("@label", "Nozzle Settings")
                            font.bold: true
                        }

                        Grid
                        {
                            columns: 2
                            columnSpacing: UM.Theme.getSize("default_margin").width
                            rowSpacing: UM.Theme.getSize("default_lining").width

                            Label
                            {
                                text: catalog.i18nc("@label", "Nozzle size")
                                visible: extruderNozzleSizeField.visible
                            }
                            Loader
                            {
                                id: extruderNozzleSizeField
                                visible: !Cura.MachineManager.hasVariants
                                sourceComponent: numericTextFieldWithUnit
                                property var propertyProvider: extruderNozzleSizeProvider
                                property string unit: catalog.i18nc("@label", "mm")
                            }

                            Label
                            {
                                text: catalog.i18nc("@label", "Nozzle offset X")
                            }
                            Loader
                            {
                                id: extruderOffsetXField
                                sourceComponent: numericTextFieldWithUnit
                                property var propertyProvider: extruderOffsetXProvider
                                property string unit: catalog.i18nc("@label", "mm")
                                property bool forceUpdateOnChange: true
                                property bool allowNegative: true
                            }
                            Label
                            {
                                text: catalog.i18nc("@label", "Nozzle offset Y")
                            }
                            Loader
                            {
                                id: extruderOffsetYField
                                sourceComponent: numericTextFieldWithUnit
                                property var propertyProvider: extruderOffsetYProvider
                                property string unit: catalog.i18nc("@label", "mm")
                                property bool forceUpdateOnChange: true
                                property bool allowNegative: true
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
                                    font.bold: true
                                }
                                TextArea
                                {
                                    id: extruderStartGcodeField
                                    width: parent.width
                                    height: parent.height - y
                                    font: UM.Theme.getFont("fixed")
                                    text: (extruderStartGcodeProvider.properties.value) ? extruderStartGcodeProvider.properties.value : ""
                                    onActiveFocusChanged:
                                    {
                                        if(!activeFocus)
                                        {
                                            extruderStartGcodeProvider.setPropertyValue("value", extruderStartGcodeField.text)
                                        }
                                    }
                                    Component.onCompleted:
                                    {
                                        wrapMode = TextEdit.NoWrap;
                                    }
                                }
                            }
                            Column {
                                height: parent.height
                                width: settingsTabs.columnWidth
                                Label
                                {
                                    text: catalog.i18nc("@label", "Extruder End Gcode")
                                    font.bold: true
                                }
                                TextArea
                                {
                                    id: extruderEndGcodeField
                                    width: parent.width
                                    height: parent.height - y
                                    font: UM.Theme.getFont("fixed")
                                    text: (extruderEndGcodeProvider.properties.value) ? extruderEndGcodeProvider.properties.value : ""
                                    onActiveFocusChanged:
                                    {
                                        if(!activeFocus)
                                        {
                                            extruderEndGcodeProvider.setPropertyValue("value", extruderEndGcodeField.text)
                                        }
                                    }
                                    Component.onCompleted:
                                    {
                                        wrapMode = TextEdit.NoWrap;
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    Component
    {
        id: numericTextFieldWithUnit
        Item {
            height: textField.height
            width: textField.width

            property bool _allowNegative: (typeof(allowNegative) === 'undefined') ? false : allowNegative
            property bool _forceUpdateOnChange: (typeof(forceUpdateOnChange) === 'undefined') ? false: forceUpdateOnChange

            TextField
            {
                id: textField
                text: (propertyProvider.properties.value) ? propertyProvider.properties.value : ""
                validator: RegExpValidator { regExp: _allowNegative ? /-?[0-9\.]{0,6}/ : /[0-9\.]{0,6}/ }
                onEditingFinished:
                {
                    if (propertyProvider && text != propertyProvider.properties.value)
                    {
                        propertyProvider.setPropertyValue("value", text);
                        if(_forceUpdateOnChange)
                        {
                            var extruderIndex = ExtruderManager.activeExtruderIndex;
                            manager.forceUpdate();
                            if(ExtruderManager.activeExtruderIndex != extruderIndex)
                            {
                                ExtruderManager.setActiveExtruderIndex(extruderIndex)
                            }
                        }
                    }
                }
            }

            Label
            {
                text: unit
                anchors.right: textField.right
                anchors.rightMargin: y - textField.y
                anchors.verticalCenter: textField.verticalCenter
            }
        }
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
        id: materialDiameterProvider

        containerStackId: Cura.MachineManager.activeMachineId
        key: "material_diameter"
        watchedProperties: [ "value" ]
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

        containerStackId: settingsTabs.currentIndex > 0 ? Cura.MachineManager.activeStackId : ""
        key: "machine_nozzle_size"
        watchedProperties: [ "value" ]
        storeIndex: manager.containerIndex
    }

    UM.SettingPropertyProvider
    {
        id: extruderOffsetXProvider

        containerStackId: settingsTabs.currentIndex > 0 ? Cura.MachineManager.activeStackId : ""
        key: "machine_nozzle_offset_x"
        watchedProperties: [ "value" ]
        storeIndex: manager.containerIndex
    }

    UM.SettingPropertyProvider
    {
        id: extruderOffsetYProvider

        containerStackId: settingsTabs.currentIndex > 0 ? Cura.MachineManager.activeStackId : ""
        key: "machine_nozzle_offset_y"
        watchedProperties: [ "value" ]
        storeIndex: manager.containerIndex
    }

    UM.SettingPropertyProvider
    {
        id: extruderStartGcodeProvider

        containerStackId: settingsTabs.currentIndex > 0 ? Cura.MachineManager.activeStackId : ""
        key: "machine_extruder_start_code"
        watchedProperties: [ "value" ]
        storeIndex: manager.containerIndex
    }

    UM.SettingPropertyProvider
    {
        id: extruderEndGcodeProvider

        containerStackId: settingsTabs.currentIndex > 0 ? Cura.MachineManager.activeStackId : ""
        key: "machine_extruder_end_code"
        watchedProperties: [ "value" ]
        storeIndex: manager.containerIndex
    }
}