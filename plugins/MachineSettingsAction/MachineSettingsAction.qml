// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1
import QtQuick.Window 2.1

import UM 1.2 as UM
import Cura 1.0 as Cura


Cura.MachineAction
{
    id: base
    property var extrudersModel: Cura.ExtrudersModel{} // Do not retrieve the Model from a backend. Otherwise the tabs
                                                       // in tabView will not removed/updated. Probably QML bug
    property int extruderTabsCount: 0

    property var activeMachineId: Cura.MachineManager.activeMachine != null ? Cura.MachineManager.activeMachine.id : ""

    Connections
    {
        target: base.extrudersModel
        onModelChanged:
        {
            var extruderCount = base.extrudersModel.count;
            base.extruderTabsCount = extruderCount;
        }
    }

    Connections
    {
        target: dialog ? dialog : null
        ignoreUnknownSignals: true
        // Any which way this action dialog is dismissed, make sure it is properly finished
        onNextClicked: finishAction()
        onBackClicked: finishAction()
        onAccepted: finishAction()
        onRejected: finishAction()
        onClosing: finishAction()
    }

    function finishAction()
    {
        forceActiveFocus();
        manager.onFinishAction();
    }

    anchors.fill: parent;
    Item
    {
        id: machineSettingsAction
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

            property real columnWidth: Math.round((width - 3 * UM.Theme.getSize("default_margin").width) / 2)
            property real labelColumnWidth: Math.round(columnWidth / 2)

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
                            spacing: UM.Theme.getSize("default_lining").height

                            Label
                            {
                                text: catalog.i18nc("@label", "Printer Settings")
                                font.bold: true
                            }

                            Item { width: UM.Theme.getSize("default_margin").width; height: UM.Theme.getSize("default_margin").height }

                            Loader
                            {
                                id: buildAreaWidthField
                                sourceComponent: numericTextFieldWithUnit
                                property string settingKey: "machine_width"
                                property string label: catalog.i18nc("@label", "X (Width)")
                                property string unit: catalog.i18nc("@label", "mm")
                                property bool forceUpdateOnChange: true
                            }

                            Loader
                            {
                                id: buildAreaDepthField
                                sourceComponent: numericTextFieldWithUnit
                                property string settingKey: "machine_depth"
                                property string label: catalog.i18nc("@label", "Y (Depth)")
                                property string unit: catalog.i18nc("@label", "mm")
                                property bool forceUpdateOnChange: true
                            }

                            Loader
                            {
                                id: buildAreaHeightField
                                sourceComponent: numericTextFieldWithUnit
                                property string settingKey: "machine_height"
                                property string label: catalog.i18nc("@label", "Z (Height)")
                                property string unit: catalog.i18nc("@label", "mm")
                                property bool forceUpdateOnChange: true
                            }

                            Item { width: UM.Theme.getSize("default_margin").width; height: UM.Theme.getSize("default_margin").height }

                            Loader
                            {
                                id: shapeComboBox
                                sourceComponent: comboBoxWithOptions
                                property string settingKey: "machine_shape"
                                property string label: catalog.i18nc("@label", "Build plate shape")
                                property bool forceUpdateOnChange: true
                            }

                            Loader
                            {
                                id: centerIsZeroCheckBox
                                sourceComponent: simpleCheckBox
                                property string settingKey: "machine_center_is_zero"
                                property string label: catalog.i18nc("@option:check", "Origin at center")
                                property bool forceUpdateOnChange: true
                            }
                            Loader
                            {
                                id: heatedBedCheckBox
                                sourceComponent: simpleCheckBox
                                property var settingKey: "machine_heated_bed"
                                property string label: catalog.i18nc("@option:check", "Heated bed")
                                property bool forceUpdateOnChange: true
                            }

                            Item { width: UM.Theme.getSize("default_margin").width; height: UM.Theme.getSize("default_margin").height }

                            Loader
                            {
                                id: gcodeFlavorComboBox
                                sourceComponent: comboBoxWithOptions
                                property string settingKey: "machine_gcode_flavor"
                                property string label: catalog.i18nc("@label", "G-code flavor")
                                property bool forceUpdateOnChange: true
                                property var afterOnActivate: manager.updateHasMaterialsMetadata
                            }
                        }

                        Column
                        {
                            width: settingsTabs.columnWidth
                            spacing: UM.Theme.getSize("default_lining").height

                            Label
                            {
                                text: catalog.i18nc("@label", "Printhead Settings")
                                font.bold: true
                            }

                            Item { width: UM.Theme.getSize("default_margin").width; height: UM.Theme.getSize("default_margin").height }

                            Loader
                            {
                                id: printheadXMinField
                                sourceComponent: headPolygonTextField
                                property string label: catalog.i18nc("@label", "X min")
                                property string tooltip: catalog.i18nc("@tooltip", "Distance from the left of the printhead to the center of the nozzle. Used to prevent colissions between previous prints and the printhead when printing \"One at a Time\".")
                                property string axis: "x"
                                property string side: "min"
                            }

                            Loader
                            {
                                id: printheadYMinField
                                sourceComponent: headPolygonTextField
                                property string label: catalog.i18nc("@label", "Y min")
                                property string tooltip: catalog.i18nc("@tooltip", "Distance from the front of the printhead to the center of the nozzle. Used to prevent colissions between previous prints and the printhead when printing \"One at a Time\".")
                                property string axis: "y"
                                property string side: "min"
                            }

                            Loader
                            {
                                id: printheadXMaxField
                                sourceComponent: headPolygonTextField
                                property string label: catalog.i18nc("@label", "X max")
                                property string tooltip: catalog.i18nc("@tooltip", "Distance from the right of the printhead to the center of the nozzle. Used to prevent colissions between previous prints and the printhead when printing \"One at a Time\".")
                                property string axis: "x"
                                property string side: "max"
                            }

                            Loader
                            {
                                id: printheadYMaxField
                                sourceComponent: headPolygonTextField
                                property string label: catalog.i18nc("@label", "Y max")
                                property string tooltip: catalog.i18nc("@tooltip", "Distance from the rear of the printhead to the center of the nozzle. Used to prevent colissions between previous prints and the printhead when printing \"One at a Time\".")
                                property string axis: "y"
                                property string side: "max"
                            }

                            Item { width: UM.Theme.getSize("default_margin").width; height: UM.Theme.getSize("default_margin").height }

                            Loader
                            {
                                id: gantryHeightField
                                sourceComponent: numericTextFieldWithUnit
                                property string settingKey: "gantry_height"
                                property string label: catalog.i18nc("@label", "Gantry height")
                                property string unit: catalog.i18nc("@label", "mm")
                                property string tooltip: catalog.i18nc("@tooltip", "The height difference between the tip of the nozzle and the gantry system (X and Y axes). Used to prevent collisions between previous prints and the gantry when printing \"One at a Time\".")
                                property bool forceUpdateOnChange: true
                            }

                            Item { width: UM.Theme.getSize("default_margin").width; height: UM.Theme.getSize("default_margin").height }

                            UM.TooltipArea
                            {
                                height: childrenRect.height
                                width: childrenRect.width
                                text: machineExtruderCountProvider.properties.description
                                visible: extruderCountModel.count >= 2

                                Row
                                {
                                    spacing: UM.Theme.getSize("default_margin").width

                                    Label
                                    {
                                        text: catalog.i18nc("@label", "Number of Extruders")
                                        elide: Text.ElideRight
                                        width: Math.max(0, settingsTabs.labelColumnWidth)
                                        anchors.verticalCenter: extruderCountComboBox.verticalCenter
                                    }
                                    ComboBox
                                    {
                                        id: extruderCountComboBox
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

                                        Connections
                                        {
                                            target: manager
                                            onDefinedExtruderCountChanged:
                                            {
                                                extruderCountModel.clear();
                                                for(var i = 0; i < manager.definedExtruderCount; ++i)
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
                                text: catalog.i18nc("@label", "Start G-code")
                                font.bold: true
                            }
                            Loader
                            {
                                id: machineStartGcodeField
                                sourceComponent: gcodeTextArea
                                property int areaWidth: parent.width
                                property int areaHeight: parent.height - y
                                property string settingKey: "machine_start_gcode"
                                property string tooltip: catalog.i18nc("@tooltip", "G-code commands to be executed at the very start.")
                            }
                        }

                        Column {
                            height: parent.height
                            width: settingsTabs.columnWidth
                            Label
                            {
                                text: catalog.i18nc("@label", "End G-code")
                                font.bold: true
                            }
                            Loader
                            {
                                id: machineEndGcodeField
                                sourceComponent: gcodeTextArea
                                property int areaWidth: parent.width
                                property int areaHeight: parent.height - y
                                property string settingKey: "machine_end_gcode"
                                property string tooltip: catalog.i18nc("@tooltip", "G-code commands to be executed at the very end.")
                            }
                        }
                    }
                }
            }

            onCurrentIndexChanged:
            {
                if(currentIndex > 0)
                {
                    contentItem.forceActiveFocus();
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
                        spacing: UM.Theme.getSize("default_lining").width

                        Label
                        {
                            text: catalog.i18nc("@label", "Nozzle Settings")
                            font.bold: true
                        }

                        Item { width: UM.Theme.getSize("default_margin").width; height: UM.Theme.getSize("default_margin").height }

                        Loader
                        {
                            id: extruderNozzleSizeField
                            visible: !Cura.MachineManager.hasVariants
                            sourceComponent: numericTextFieldWithUnit
                            property string settingKey: "machine_nozzle_size"
                            property string label: catalog.i18nc("@label", "Nozzle size")
                            property string unit: catalog.i18nc("@label", "mm")
                            function afterOnEditingFinished()
                            {
                                // Somehow the machine_nozzle_size dependent settings are not updated otherwise
                                Cura.MachineManager.forceUpdateAllSettings()
                            }
                            property bool isExtruderSetting: true
                        }

                        Loader
                        {
                            id: materialDiameterField
                            visible: Cura.MachineManager.hasMaterials
                            sourceComponent: numericTextFieldWithUnit
                            property string settingKey: "material_diameter"
                            property string label: catalog.i18nc("@label", "Compatible material diameter")
                            property string unit: catalog.i18nc("@label", "mm")
                            property string tooltip: catalog.i18nc("@tooltip", "The nominal diameter of filament supported by the printer. The exact diameter will be overridden by the material and/or the profile.")
                            function afterOnEditingFinished()
                            {
                                if (settingsTabs.currentIndex > 0)
                                {
                                    manager.updateMaterialForDiameter(settingsTabs.currentIndex - 1)
                                }
                            }
                            function setValueFunction(value)
                            {
                                if (settingsTabs.currentIndex > 0)
                                {
                                    const extruderIndex = index.toString()
                                    Cura.MachineManager.activeMachine.extruders[extruderIndex].compatibleMaterialDiameter = value
                                }
                            }
                            property bool isExtruderSetting: true
                        }

                        Loader
                        {
                            id: extruderOffsetXField
                            sourceComponent: numericTextFieldWithUnit
                            property string settingKey: "machine_nozzle_offset_x"
                            property string label: catalog.i18nc("@label", "Nozzle offset X")
                            property string unit: catalog.i18nc("@label", "mm")
                            property bool isExtruderSetting: true
                            property bool forceUpdateOnChange: true
                            property bool allowNegative: true
                        }

                        Loader
                        {
                            id: extruderOffsetYField
                            sourceComponent: numericTextFieldWithUnit
                            property string settingKey: "machine_nozzle_offset_y"
                            property string label: catalog.i18nc("@label", "Nozzle offset Y")
                            property string unit: catalog.i18nc("@label", "mm")
                            property bool isExtruderSetting: true
                            property bool forceUpdateOnChange: true
                            property bool allowNegative: true
                        }

                        Loader
                        {
                            id: extruderCoolingFanNumberField
                            sourceComponent: numericTextFieldWithUnit
                            property string settingKey: "machine_extruder_cooling_fan_number"
                            property string label: catalog.i18nc("@label", "Cooling Fan Number")
                            property string unit: catalog.i18nc("@label", "")
                            property bool isExtruderSetting: true
                            property bool forceUpdateOnChange: true
                            property bool allowNegative: false
                        }

                        Item { width: UM.Theme.getSize("default_margin").width; height: UM.Theme.getSize("default_margin").height }

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
                                    text: catalog.i18nc("@label", "Extruder Start G-code")
                                    font.bold: true
                                }
                                Loader
                                {
                                    id: extruderStartGcodeField
                                    sourceComponent: gcodeTextArea
                                    property int areaWidth: parent.width
                                    property int areaHeight: parent.height - y
                                    property string settingKey: "machine_extruder_start_code"
                                    property bool isExtruderSetting: true
                                }
                            }
                            Column {
                                height: parent.height
                                width: settingsTabs.columnWidth
                                Label
                                {
                                    text: catalog.i18nc("@label", "Extruder End G-code")
                                    font.bold: true
                                }
                                Loader
                                {
                                    id: extruderEndGcodeField
                                    sourceComponent: gcodeTextArea
                                    property int areaWidth: parent.width
                                    property int areaHeight: parent.height - y
                                    property string settingKey: "machine_extruder_end_code"
                                    property bool isExtruderSetting: true
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
        id: simpleCheckBox
        UM.TooltipArea
        {
            height: checkBox.height
            width: checkBox.width
            text: _tooltip

            property bool _isExtruderSetting: (typeof(isExtruderSetting) === 'undefined') ? false: isExtruderSetting
            property bool _forceUpdateOnChange: (typeof(forceUpdateOnChange) === 'undefined') ? false: forceUpdateOnChange
            property string _tooltip: (typeof(tooltip) === 'undefined') ? propertyProvider.properties.description : tooltip

            UM.SettingPropertyProvider
            {
                id: propertyProvider

                containerStackId: {
                    if(_isExtruderSetting)
                    {
                        if(settingsTabs.currentIndex > 0)
                        {
                            return Cura.ExtruderManager.extruderIds[String(settingsTabs.currentIndex - 1)];
                        }
                        return "";
                    }
                    return base.activeMachineId
                }
                key: settingKey
                watchedProperties: [ "value", "description" ]
                storeIndex: manager.containerIndex
            }

            CheckBox
            {
                id: checkBox
                text: label
                checked: String(propertyProvider.properties.value).toLowerCase() != 'false'
                onClicked:
                {
                    propertyProvider.setPropertyValue("value", checked);
                    if(_forceUpdateOnChange)
                    {
                        manager.forceUpdate();
                    }
                }
            }
        }
    }

    Component
    {
        id: numericTextFieldWithUnit
        UM.TooltipArea
        {
            height: childrenRect.height
            width: childrenRect.width
            text: _tooltip

            property bool _isExtruderSetting: (typeof(isExtruderSetting) === 'undefined') ? false: isExtruderSetting
            property bool _allowNegative: (typeof(allowNegative) === 'undefined') ? false : allowNegative
            property var _afterOnEditingFinished: (typeof(afterOnEditingFinished) === 'undefined') ? undefined : afterOnEditingFinished
            property bool _forceUpdateOnChange: (typeof(forceUpdateOnChange) === 'undefined') ? false : forceUpdateOnChange
            property string _label: (typeof(label) === 'undefined') ? "" : label
            property string _tooltip: (typeof(tooltip) === 'undefined') ? propertyProvider.properties.description : tooltip
            property var _setValueFunction: (typeof(setValueFunction) === 'undefined') ? undefined : setValueFunction

            UM.SettingPropertyProvider
            {
                id: propertyProvider

                containerStackId: {
                    if(_isExtruderSetting)
                    {
                        if(settingsTabs.currentIndex > 0)
                        {
                            return Cura.ExtruderManager.extruderIds[String(settingsTabs.currentIndex - 1)];
                        }
                        return "";
                    }
                    return base.activeMachineId
                }
                key: settingKey
                watchedProperties: [ "value", "description" ]
                storeIndex: manager.containerIndex
            }

            Row
            {
                spacing: UM.Theme.getSize("default_margin").width

                Label
                {
                    text: _label
                    visible: _label != ""
                    elide: Text.ElideRight
                    width: Math.max(0, settingsTabs.labelColumnWidth)
                    anchors.verticalCenter: textFieldWithUnit.verticalCenter
                }

                Item
                {
                    width: textField.width
                    height: textField.height

                    id: textFieldWithUnit
                    TextField
                    {
                        id: textField
                        text: {
                            const value = propertyProvider.properties.value;
                            return value ? value : "";
                        }
                        validator: RegExpValidator { regExp: _allowNegative ? /-?[0-9\.,]{0,6}/ : /[0-9\.,]{0,6}/ }
                        onEditingFinished:
                        {
                            if (propertyProvider && text != propertyProvider.properties.value)
                            {
                                // For some properties like the extruder-compatible material diameter, they need to
                                // trigger many updates, such as the available materials, the current material may
                                // need to be switched, etc. Although setting the diameter can be done directly via
                                // the provider, all the updates that need to be triggered then need to depend on
                                // the metadata update, a signal that can be fired way too often. The update functions
                                // can have if-checks to filter out the irrelevant updates, but still it incurs unnecessary
                                // overhead.
                                // The ExtruderStack class has a dedicated function for this call "setCompatibleMaterialDiameter()",
                                // and it triggers the diameter update signals only when it is needed. Here it is optionally
                                // choose to use setCompatibleMaterialDiameter() or other more specific functions that
                                // are available.
                                if (_setValueFunction !== undefined)
                                {
                                    _setValueFunction(text)
                                }
                                else
                                {
                                    propertyProvider.setPropertyValue("value", text)
                                }
                                if(_forceUpdateOnChange)
                                {
                                    manager.forceUpdate()
                                }
                                if(_afterOnEditingFinished)
                                {
                                    _afterOnEditingFinished()
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
        }
    }

    Component
    {
        id: comboBoxWithOptions
        UM.TooltipArea
        {
            height: childrenRect.height
            width: childrenRect.width
            text: _tooltip

            property bool _isExtruderSetting: (typeof(isExtruderSetting) === 'undefined') ? false : isExtruderSetting
            property bool _forceUpdateOnChange: (typeof(forceUpdateOnChange) === 'undefined') ? false : forceUpdateOnChange
            property var _afterOnActivate: (typeof(afterOnActivate) === 'undefined') ? undefined : afterOnActivate
            property string _label: (typeof(label) === 'undefined') ? "" : label
            property string _tooltip: (typeof(tooltip) === 'undefined') ? propertyProvider.properties.description : tooltip

            UM.SettingPropertyProvider
            {
                id: propertyProvider

                containerStackId: {
                    if(_isExtruderSetting)
                    {
                        if(settingsTabs.currentIndex > 0)
                        {
                            return Cura.ExtruderManager.extruderIds[String(settingsTabs.currentIndex - 1)];
                        }
                        return "";
                    }
                    return base.activeMachineId
                }
                key: settingKey
                watchedProperties: [ "value", "options", "description" ]
                storeIndex: manager.containerIndex
            }

            Row
            {
                spacing: UM.Theme.getSize("default_margin").width

                Label
                {
                    text: _label
                    visible: _label != ""
                    elide: Text.ElideRight
                    width: Math.max(0, settingsTabs.labelColumnWidth)
                    anchors.verticalCenter: comboBox.verticalCenter
                }
                ComboBox
                {
                    id: comboBox
                    model: ListModel
                    {
                        id: optionsModel
                        Component.onCompleted:
                        {
                            // Options come in as a string-representation of an OrderedDict
                            var options = propertyProvider.properties.options.match(/^OrderedDict\(\[\((.*)\)\]\)$/);
                            if(options)
                            {
                                options = options[1].split("), (")
                                for(var i = 0; i < options.length; i++)
                                {
                                    var option = options[i].substring(1, options[i].length - 1).split("', '")
                                    optionsModel.append({text: option[1], value: option[0]});
                                }
                            }
                        }
                    }
                    currentIndex:
                    {
                        var currentValue = propertyProvider.properties.value;
                        var index = 0;
                        for(var i = 0; i < optionsModel.count; i++)
                        {
                            if(optionsModel.get(i).value == currentValue) {
                                index = i;
                                break;
                            }
                        }
                        return index
                    }
                    onActivated:
                    {
                        if(propertyProvider.properties.value != optionsModel.get(index).value)
                        {
                            propertyProvider.setPropertyValue("value", optionsModel.get(index).value);
                            if(_forceUpdateOnChange)
                            {
                                manager.forceUpdate();
                            }
                            if(_afterOnActivate)
                            {
                                _afterOnActivate();
                            }
                        }
                    }
                }
            }
        }
    }

    Component
    {
        id: gcodeTextArea

        UM.TooltipArea
        {
            height: gcodeArea.height
            width: gcodeArea.width
            text: _tooltip

            property bool _isExtruderSetting: (typeof(isExtruderSetting) === 'undefined') ? false : isExtruderSetting
            property string _tooltip: (typeof(tooltip) === 'undefined') ? propertyProvider.properties.description : tooltip

            UM.SettingPropertyProvider
            {
                id: propertyProvider

                containerStackId: {
                    if(_isExtruderSetting)
                    {
                        if(settingsTabs.currentIndex > 0)
                        {
                            return Cura.ExtruderManager.extruderIds[String(settingsTabs.currentIndex - 1)];
                        }
                        return "";
                    }
                    return base.activeMachineId
                }
                key: settingKey
                watchedProperties: [ "value", "description" ]
                storeIndex: manager.containerIndex
            }

            TextArea
            {
                id: gcodeArea
                width: areaWidth
                height: areaHeight
                font: UM.Theme.getFont("fixed")
                text: (propertyProvider.properties.value) ? propertyProvider.properties.value : ""
                onActiveFocusChanged:
                {
                    if(!activeFocus)
                    {
                        propertyProvider.setPropertyValue("value", gcodeArea.text)
                    }
                }
                Component.onCompleted:
                {
                    wrapMode = TextEdit.NoWrap;
                }
            }
        }
    }

    Component
    {
        id: headPolygonTextField
        UM.TooltipArea
        {
            height: textField.height
            width: textField.width
            text: tooltip

            property string _label: (typeof(label) === 'undefined') ? "" : label

            Row
            {
                spacing: UM.Theme.getSize("default_margin").width

                Label
                {
                    text: _label
                    visible: _label != ""
                    elide: Text.ElideRight
                    width: Math.max(0, settingsTabs.labelColumnWidth)
                    anchors.verticalCenter: textFieldWithUnit.verticalCenter
                }

                Item
                {
                    id: textFieldWithUnit
                    width: textField.width
                    height: textField.height

                    TextField
                    {
                        id: textField
                        text:
                        {
                            var polygon = JSON.parse(machineHeadPolygonProvider.properties.value);
                            var item = (axis == "x") ? 0 : 1
                            var result = polygon[0][item];
                            for(var i = 1; i < polygon.length; i++) {
                                if (side == "min") {
                                    result = Math.min(result, polygon[i][item]);
                                } else {
                                    result = Math.max(result, polygon[i][item]);
                                }
                            }
                            result = Math.abs(result);
                            printHeadPolygon[axis][side] = result;
                            return result;
                        }
                        validator: RegExpValidator { regExp: /[0-9\.,]{0,6}/ }
                        onEditingFinished:
                        {
                            printHeadPolygon[axis][side] = parseFloat(textField.text.replace(',','.'));
                            var polygon = [];
                            polygon.push([-printHeadPolygon["x"]["min"], printHeadPolygon["y"]["max"]]);
                            polygon.push([-printHeadPolygon["x"]["min"],-printHeadPolygon["y"]["min"]]);
                            polygon.push([ printHeadPolygon["x"]["max"], printHeadPolygon["y"]["max"]]);
                            polygon.push([ printHeadPolygon["x"]["max"],-printHeadPolygon["y"]["min"]]);
                            var polygon_string = JSON.stringify(polygon);
                            if(polygon_string != machineHeadPolygonProvider.properties.value)
                            {
                                machineHeadPolygonProvider.setPropertyValue("value", polygon_string);
                                manager.forceUpdate();
                            }
                        }
                    }

                    Label
                    {
                        text: catalog.i18nc("@label", "mm")
                        anchors.right: textField.right
                        anchors.rightMargin: y - textField.y
                        anchors.verticalCenter: textField.verticalCenter
                    }
                }
            }
        }
    }

    property var printHeadPolygon:
    {
        "x": {
            "min": 0,
            "max": 0,
        },
        "y": {
            "min": 0,
            "max": 0,
        },
    }


    UM.SettingPropertyProvider
    {
        id: machineExtruderCountProvider

        containerStackId: base.activeMachineId
        key: "machine_extruder_count"
        watchedProperties: [ "value", "description" ]
        storeIndex: manager.containerIndex
    }

    UM.SettingPropertyProvider
    {
        id: machineHeadPolygonProvider

        containerStackId: base.activeMachineId
        key: "machine_head_with_fans_polygon"
        watchedProperties: [ "value" ]
        storeIndex: manager.containerIndex
    }
}
