// Copyright (c) 2016 Ultimaker B.V.
// Uranium is released under the terms of the AGPLv3 or higher.

import QtQuick 2.1
import QtQuick.Controls 1.3
import QtQuick.Dialogs 1.2

import UM 1.2 as UM
import Cura 1.0 as Cura

TabView
{
    id: base

    property QtObject properties;

    property bool editingEnabled: false;
    property string currency: UM.Preferences.getValue("cura/currency") ? UM.Preferences.getValue("cura/currency") : "€"
    property real firstColumnWidth: width * 0.45
    property real secondColumnWidth: width * 0.45
    property string containerId: ""
    property var materialPreferenceValues: UM.Preferences.getValue("cura/material_settings") ? JSON.parse(UM.Preferences.getValue("cura/material_settings")) : {}

    property double spoolLength: calculateSpoolLength()
    property real costPerMeter: calculateCostPerMeter()

    Tab
    {
        title: catalog.i18nc("@title","Information")

        anchors
        {
            leftMargin: UM.Theme.getSize("default_margin").width
            topMargin: UM.Theme.getSize("default_margin").height
            bottomMargin: UM.Theme.getSize("default_margin").height
            rightMargin: 0
        }

        ScrollView
        {
            anchors.fill: parent
            horizontalScrollBarPolicy: Qt.ScrollBarAlwaysOff
            flickableItem.flickableDirection: Flickable.VerticalFlick

            Flow
            {
                id: containerGrid

                width: base.width;

                property real rowHeight: textField.height;

                Label { width: base.firstColumnWidth; height: parent.rowHeight; verticalAlignment: Qt.AlignVCenter; text: catalog.i18nc("@label", "Display Name") }
                ReadOnlyTextField
                {
                    id: displayNameTextField;
                    width: base.secondColumnWidth;
                    text: properties.name;
                    readOnly: !base.editingEnabled;
                    onEditingFinished: base.setName(properties.name, text)
                }

                Label { width: base.firstColumnWidth; height: parent.rowHeight; verticalAlignment: Qt.AlignVCenter; text: catalog.i18nc("@label", "Brand") }
                ReadOnlyTextField
                {
                    id: textField;
                    width: base.secondColumnWidth;
                    text: properties.supplier;
                    readOnly: !base.editingEnabled;
                    onEditingFinished: base.setMetaDataEntry("brand", properties.supplier, text)
                }

                Label { width: base.firstColumnWidth; height: parent.rowHeight; verticalAlignment: Qt.AlignVCenter; text: catalog.i18nc("@label", "Material Type") }
                ReadOnlyTextField
                {
                    width: base.secondColumnWidth;
                    text: properties.material_type;
                    readOnly: !base.editingEnabled;
                    onEditingFinished: base.setMetaDataEntry("material", properties.material_type, text)
                }

                Label { width: base.firstColumnWidth; height: parent.rowHeight; verticalAlignment: Qt.AlignVCenter; text: catalog.i18nc("@label", "Color") }

                Row
                {
                    width: base.secondColumnWidth;
                    height:  parent.rowHeight;
                    spacing: UM.Theme.getSize("default_margin").width/2

                    Rectangle
                    {
                        id: colorSelector
                        color: properties.color_code

                        width: colorLabel.height * 0.75
                        height: colorLabel.height * 0.75
                        border.width: UM.Theme.getSize("default_lining").height

                        anchors.verticalCenter: parent.verticalCenter

                        MouseArea { anchors.fill: parent; onClicked: colorDialog.open(); enabled: base.editingEnabled }
                    }
                    ReadOnlyTextField
                    {
                        id: colorLabel;
                        text: properties.color_name;
                        readOnly: !base.editingEnabled
                        onEditingFinished: base.setMetaDataEntry("color_name", properties.color_name, text)
                    }

                    ColorDialog { id: colorDialog; color: properties.color_code; onAccepted: base.setMetaDataEntry("color_code", properties.color_code, color) }
                }

                Item { width: parent.width; height: UM.Theme.getSize("default_margin").height }

                Label { width: parent.width; height: parent.rowHeight; font.bold: true; verticalAlignment: Qt.AlignVCenter; text: catalog.i18nc("@label", "Properties") }

                Label { width: base.firstColumnWidth; height: parent.rowHeight; verticalAlignment: Qt.AlignVCenter; text: catalog.i18nc("@label", "Density") }
                ReadOnlySpinBox
                {
                    id: densitySpinBox
                    width: base.secondColumnWidth
                    value: properties.density
                    decimals: 2
                    suffix: " g/cm³"
                    stepSize: 0.01
                    readOnly: !base.editingEnabled

                    onEditingFinished: base.setMetaDataEntry("properties/density", properties.density, value)
                    onValueChanged: updateCostPerMeter()
                }

                Label { width: base.firstColumnWidth; height: parent.rowHeight; verticalAlignment: Qt.AlignVCenter; text: catalog.i18nc("@label", "Diameter") }
                ReadOnlySpinBox
                {
                    id: diameterSpinBox
                    width: base.secondColumnWidth
                    value: properties.diameter
                    decimals: 2
                    suffix: " mm"
                    stepSize: 0.01
                    readOnly: !base.editingEnabled

                    onEditingFinished: base.setMetaDataEntry("properties/diameter", properties.diameter, value)
                    onValueChanged: updateCostPerMeter()
                }

                Label { width: base.firstColumnWidth; height: parent.rowHeight; verticalAlignment: Qt.AlignVCenter; text: catalog.i18nc("@label", "Filament Cost") }
                SpinBox
                {
                    id: spoolCostSpinBox
                    width: base.secondColumnWidth
                    value: base.getMaterialPreferenceValue(properties.guid, "spool_cost")
                    prefix: base.currency + " "
                    decimals: 2
                    maximumValue: 1000

                    onEditingFinished: base.setMaterialPreferenceValue(properties.guid, "spool_cost", parseFloat(value))
                    onValueChanged: updateCostPerMeter()
                }

                Label { width: base.firstColumnWidth; height: parent.rowHeight; verticalAlignment: Qt.AlignVCenter; text: catalog.i18nc("@label", "Filament weight") }
                SpinBox
                {
                    id: spoolWeightSpinBox
                    width: base.secondColumnWidth
                    value: base.getMaterialPreferenceValue(properties.guid, "spool_weight")
                    suffix: " g"
                    stepSize: 100
                    decimals: 0
                    maximumValue: 10000

                    onEditingFinished: base.setMaterialPreferenceValue(properties.guid, "spool_weight", parseFloat(value))
                    onValueChanged: updateCostPerMeter()
                }

                Label { width: base.firstColumnWidth; height: parent.rowHeight; verticalAlignment: Qt.AlignVCenter; text: catalog.i18nc("@label", "Filament length") }
                Label
                {
                    width: base.secondColumnWidth
                    text: "~ %1 m".arg(Math.round(base.spoolLength))
                    verticalAlignment: Qt.AlignVCenter
                    height: parent.rowHeight
                }

                Label { width: base.firstColumnWidth; height: parent.rowHeight; verticalAlignment: Qt.AlignVCenter; text: catalog.i18nc("@label", "Cost per Meter") }
                Label
                {
                    width: base.secondColumnWidth
                    text: "~ %1 %2/m".arg(base.costPerMeter.toFixed(2)).arg(base.currency)
                    verticalAlignment: Qt.AlignVCenter
                    height: parent.rowHeight
                }

                Item { width: parent.width; height: UM.Theme.getSize("default_margin").height }

                Label { width: parent.width; height: parent.rowHeight; verticalAlignment: Qt.AlignVCenter; text: catalog.i18nc("@label", "Description") }

                ReadOnlyTextArea
                {
                    text: properties.description;
                    width: base.firstColumnWidth + base.secondColumnWidth
                    wrapMode: Text.WordWrap

                    readOnly: !base.editingEnabled;

                    onEditingFinished: base.setMetaDataEntry("description", properties.description, text)
                }

                Label { width: parent.width; height: parent.rowHeight; verticalAlignment: Qt.AlignVCenter; text: catalog.i18nc("@label", "Adhesion Information") }

                ReadOnlyTextArea
                {
                    text: properties.adhesion_info;
                    width: base.firstColumnWidth + base.secondColumnWidth
                    wrapMode: Text.WordWrap

                    readOnly: !base.editingEnabled;

                    onEditingFinished: base.setMetaDataEntry("adhesion_info", properties.adhesion_info, text)
                }
            }

            function updateCostPerMeter()
            {
                base.spoolLength = calculateSpoolLength(diameterSpinBox.value, densitySpinBox.value, spoolWeightSpinBox.value);
                base.costPerMeter = calculateCostPerMeter(spoolCostSpinBox.value);
            }
        }
    }

    Tab
    {
        title: catalog.i18nc("@label", "Print settings")
        anchors
        {
            leftMargin: UM.Theme.getSize("default_margin").width
            topMargin: UM.Theme.getSize("default_margin").height
            bottomMargin: UM.Theme.getSize("default_margin").height
            rightMargin: 0
        }

        ScrollView
        {
            anchors.fill: parent;

            ListView
            {
                model: UM.SettingDefinitionsModel
                {
                    containerId: Cura.MachineManager.activeDefinitionId
                    visibilityHandler: Cura.MaterialSettingsVisibilityHandler { }
                    expanded: ["*"]
                }

                delegate: UM.TooltipArea
                {
                    width: childrenRect.width
                    height: childrenRect.height
                    text: model.description
                    Label
                    {
                        id: label
                        width: base.firstColumnWidth;
                        height: spinBox.height
                        text: model.label
                    }
                    ReadOnlySpinBox
                    {
                        id: spinBox
                        anchors.left: label.right
                        value: parseFloat(provider.properties.value);
                        width: base.secondColumnWidth;
                        readOnly: !base.editingEnabled
                        suffix: model.unit
                        maximumValue: 99999
                        decimals: model.unit == "mm" ? 2 : 0

                        onEditingFinished: provider.setPropertyValue("value", value)
                    }

                    UM.ContainerPropertyProvider { id: provider; containerId: base.containerId; watchedProperties: [ "value" ]; key: model.key }
                }
            }
        }
    }

    function calculateSpoolLength(diameter, density, spoolWeight)
    {
        if(!diameter)
        {
            diameter = properties.diameter;
        }
        if(!density)
        {
            density = properties.density;
        }
        if(!spoolWeight)
        {
            spoolWeight = base.getMaterialPreferenceValue(properties.guid, "spool_weight");
        }

        if (diameter == 0 || density == 0 || spoolWeight == 0)
        {
            return 0;
        }
        var area = Math.PI * Math.pow(diameter / 2, 2); // in mm2
        var volume = (spoolWeight / density); // in cm3
        return volume / area; // in m
    }

    function calculateCostPerMeter(spoolCost)
    {
        if(!spoolCost)
        {
            spoolCost = base.getMaterialPreferenceValue(properties.guid, "spool_cost");
        }

        if (spoolLength == 0)
        {
            return 0;
        }
        return spoolCost / spoolLength;
    }

    // Tiny convenience function to check if a value really changed before trying to set it.
    function setMetaDataEntry(entry_name, old_value, new_value)
    {
        if(old_value != new_value)
        {
            Cura.ContainerManager.setContainerMetaDataEntry(base.containerId, entry_name, new_value);
        }
    }

    function setMaterialPreferenceValue(material_guid, entry_name, new_value)
    {
        if(!(material_guid in materialPreferenceValues))
        {
            materialPreferenceValues[material_guid] = {};
        }
        if(entry_name in materialPreferenceValues[material_guid] && materialPreferenceValues[material_guid][entry_name] == new_value)
        {
            // value has not changed
            return
        }
        materialPreferenceValues[material_guid][entry_name] = new_value;

        // store preference
        UM.Preferences.setValue("cura/material_settings", JSON.stringify(materialPreferenceValues));
    }

    function getMaterialPreferenceValue(material_guid, entry_name)
    {
        if(material_guid in materialPreferenceValues && entry_name in materialPreferenceValues[material_guid])
        {
            return materialPreferenceValues[material_guid][entry_name];
        }
        return 0;
    }

    function setName(old_value, new_value)
    {
        if(old_value != new_value)
        {
            Cura.ContainerManager.setContainerName(base.containerId, new_value);
            // update material name label. not so pretty, but it works
            materialProperties.name = new_value;
        }
    }
}
