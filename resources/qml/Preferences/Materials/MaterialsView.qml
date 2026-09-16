// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.3
import QtQuick.Dialogs

import UM 1.5 as UM
import Cura 1.0 as Cura

Item
{
    id: base

    property QtObject properties
    property var currentMaterialNode: null

    property bool editingEnabled: false
    property string currency: UM.Preferences.getValue("cura/currency") ? UM.Preferences.getValue("cura/currency") : "€"
    property string containerId: ""
    property var materialPreferenceValues: UM.Preferences.getValue("cura/material_settings") ? JSON.parse(UM.Preferences.getValue("cura/material_settings")) : {}
    property var materialManagementModel: CuraApplication.getMaterialManagementModel()

    property double spoolLength: calculateSpoolLength()
    property real costPerMeter: calculateCostPerMeter()

    signal resetSelectedMaterial()

    property bool reevaluateLinkedMaterials: false
    property string linkedMaterialNames:
    {
        if (reevaluateLinkedMaterials)
        {
            reevaluateLinkedMaterials = false;
        }
        if (!base.containerId || !base.editingEnabled || !base.currentMaterialNode)
        {
            return "";
        }
        var linkedMaterials = Cura.ContainerManager.getLinkedMaterials(base.currentMaterialNode, true);
        if (linkedMaterials.length == 0)
        {
            return "";
        }
        return linkedMaterials.join(", ");
    }

    function getApproximateDiameter(diameter)
    {
        return Math.round(diameter);
    }

    // This trick makes sure to make all fields lose focus so their onEditingFinished will be triggered
    // and modified values will be saved. This can happen when a user changes a value and then closes the
    // dialog directly.
    //
    // Please note that somehow this callback is ONLY triggered when visible is false.
    onVisibleChanged:
    {
        if (!visible)
        {
            base.focus = false;
        }
    }

    Rectangle
    {
        color: UM.Theme.getColor("main_background")

        anchors
        {
            top: pageSelectorTabRow.bottom
            topMargin: -UM.Theme.getSize("default_lining").width
            left: parent.left
            right: parent.right
            bottom: parent.bottom
        }
        border.width: UM.Theme.getSize("default_lining").width
        border.color: UM.Theme.getColor("border_main")

        ScrollView
        {
            id: informationPage
            anchors
            {
                fill: parent
                topMargin: UM.Theme.getSize("thin_margin").height
                bottomMargin: UM.Theme.getSize("thin_margin").height
                leftMargin: UM.Theme.getSize("thin_margin").width
                rightMargin: UM.Theme.getSize("thin_margin").width
            }

            ScrollBar.vertical: UM.ScrollBar
            {
                id: scrollBar
                parent: informationPage.parent
                anchors
                {
                    top: parent.top
                    right: parent.right
                    bottom: parent.bottom
                }
            }
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
            clip: true
            visible: pageSelectorTabRow.currentItem.activeView === "information"

            property real columnWidth: Math.floor((width - scrollBar.width - UM.Theme.getSize("narrow_margin").width) / 2)
            property real rowHeight: UM.Theme.getSize("setting_control").height

            Column
            {
                width: informationPage.width
                spacing: UM.Theme.getSize("narrow_margin").height

                Cura.MessageDialog
                {
                    id: confirmDiameterChangeDialog

                    title: catalog.i18nc("@title:window", "Confirm Diameter Change")
                    text: catalog.i18nc("@label (%1 is a number)", "The new filament diameter is set to %1 mm, which is not compatible with the current extruder. Do you wish to continue?".arg(new_diameter_value))
                    standardButtons: Dialog.Yes | Dialog.No

                    property var new_diameter_value: null
                    property var old_diameter_value: null
                    property var old_approximate_diameter_value: null

                    onAccepted:
                    {
                        base.setMetaDataEntry("approximate_diameter", old_approximate_diameter_value, getApproximateDiameter(new_diameter_value).toString());
                        base.setMetaDataEntry("properties/diameter", properties.diameter, new_diameter_value);
                        // CURA-6868 Make sure to update the extruder to user a diameter-compatible material.
                        Cura.MachineManager.updateMaterialWithVariant()
                        base.resetSelectedMaterial()
                    }

                    onRejected:
                    {
                        base.properties.diameter = old_diameter_value;
                        diameterTextField.valueText = Qt.binding(function() { return base.properties.diameter })
                    }
                }

                Row
                {
                    spacing: UM.Theme.getSize("narrow_margin").width
                    UM.Label
                    {
                        height: informationPage.rowHeight
                        width: informationPage.columnWidth
                        text: catalog.i18nc("@label", "Display Name")
                    }
                    Cura.TextField
                    {
                        id: displayNameTextField
                        width: informationPage.columnWidth
                        text: properties.name
                        enabled: base.editingEnabled
                        onEditingFinished: base.updateMaterialDisplayName(properties.name, text)
                    }
                }

                Row
                {
                    spacing: UM.Theme.getSize("narrow_margin").width
                    UM.Label
                    {
                        height: informationPage.rowHeight
                        width: informationPage.columnWidth
                        text: catalog.i18nc("@label", "Brand")
                    }
                    Cura.TextField
                    {
                        id: brandTextField
                        width: informationPage.columnWidth
                        text: properties.brand
                        enabled: base.editingEnabled
                        onEditingFinished: base.updateMaterialBrand(properties.brand, text)
                    }
                }

                Row
                {
                    spacing: UM.Theme.getSize("narrow_margin").width
                    UM.Label
                    {
                        height: informationPage.rowHeight
                        width: informationPage.columnWidth
                        text: catalog.i18nc("@label", "Material Type")
                    }
                    Cura.TextField
                    {
                        id: materialTypeField
                        width: informationPage.columnWidth
                        text: properties.material
                        enabled: base.editingEnabled
                        onEditingFinished: base.updateMaterialType(properties.material, text)
                    }
                }

                Row
                {
                    spacing: UM.Theme.getSize("narrow_margin").width
                    UM.Label
                    {
                        height: informationPage.rowHeight
                        width: informationPage.columnWidth
                        verticalAlignment: Qt.AlignVCenter
                        text: catalog.i18nc("@label", "Color")
                    }

                    Row
                    {
                        width: informationPage.columnWidth
                        spacing: Math.round(UM.Theme.getSize("default_margin").width / 2)

                        // color indicator square
                        Item
                        {
                            id: colorSelector

                            anchors.verticalCenter: parent.verticalCenter

                            width: colorSelectorBackground.width + 2 * UM.Theme.getSize("narrow_margin").width
                            height: colorSelectorBackground.height + 2 * UM.Theme.getSize("narrow_margin").height

                            Rectangle
                            {
                                id: colorSelectorBackground
                                color: properties.color_code
                                width: UM.Theme.getSize("icon_indicator").width
                                height: UM.Theme.getSize("icon_indicator").height
                                radius: width / 2
                                anchors.centerIn: parent
                            }

                            // open the color selection dialog on click
                            MouseArea
                            {
                                anchors.fill: parent
                                onClicked: colorDialog.open()
                                enabled: base.editingEnabled
                            }
                        }

                        // pretty color name text field
                        Cura.TextField
                        {
                            id: colorLabel;
                            width: parent.width - colorSelector.width - parent.spacing
                            text: properties.color_name;
                            enabled: base.editingEnabled
                            onEditingFinished: base.setMetaDataEntry("color_name", properties.color_name, text)
                        }

                        // popup dialog to select a new color
                        // if successful it sets the properties.color_code value to the new color
                        ColorDialog
                        {
                            id: colorDialog
                            title: catalog.i18nc("@title", "Material color picker")
                            selectedColor: properties.color_code
                            onAccepted: base.setMetaDataEntry("color_code", properties.color_code, selectedColor)
                        }
                    }
                }

                UM.Label
                {
                    width: parent.width
                    height: parent.rowHeight
                    font: UM.Theme.getFont("default_bold")
                    verticalAlignment: Qt.AlignVCenter
                    text: catalog.i18nc("@label", "Properties")
                }

                Row
                {
                    height: parent.rowHeight
                    spacing: UM.Theme.getSize("narrow_margin").width
                    UM.Label
                    {
                        height: informationPage.rowHeight
                        width: informationPage.columnWidth
                        text: catalog.i18nc("@label", "Density")
                    }

                    Cura.NumericTextFieldWithUnit
                    {
                        id: densityTextField
                        enabled: base.editingEnabled
                        valueText: properties.density
                        controlWidth: informationPage.columnWidth
                        controlHeight: informationPage.rowHeight
                        spacing: 0
                        unitText: "g/cm³"
                        decimals: 2
                        maximum: 1000

                        editingFinishedFunction: function()
                        {
                            var modified_text = valueText.replace(",", ".");
                            base.setMetaDataEntry("properties/density", properties.density, modified_text)
                        }

                        onValueTextChanged: updateCostPerMeter()
                    }
                }

                Row
                {
                    height: parent.rowHeight
                    spacing: UM.Theme.getSize("narrow_margin").width
                    UM.Label
                    {
                        height: informationPage.rowHeight
                        width: informationPage.columnWidth
                        text: catalog.i18nc("@label", "Diameter")
                    }

                    Cura.NumericTextFieldWithUnit
                    {
                        id: diameterTextField
                        enabled: base.editingEnabled
                        valueText: properties.diameter
                        controlWidth: informationPage.columnWidth
                        controlHeight: informationPage.rowHeight
                        spacing: 0
                        unitText: "mm"
                        decimals: 2
                        maximum: 1000

                        editingFinishedFunction: function()
                        {
                            // This does not use a SettingPropertyProvider, because we need to make the change to all containers
                            // which derive from the same base_file
                            var old_diameter = Cura.ContainerManager.getContainerMetaDataEntry(base.containerId, "properties/diameter");
                            var old_approximate_diameter = Cura.ContainerManager.getContainerMetaDataEntry(base.containerId, "approximate_diameter");
                            var modified_value = valueText.replace(",", ".");
                            var new_approximate_diameter = getApproximateDiameter(modified_value);

                            if (new_approximate_diameter != Cura.ExtruderManager.getActiveExtruderStack().approximateMaterialDiameter)
                            {
                                confirmDiameterChangeDialog.old_diameter_value = old_diameter;
                                confirmDiameterChangeDialog.new_diameter_value = modified_value;
                                confirmDiameterChangeDialog.old_approximate_diameter_value = old_approximate_diameter;

                                confirmDiameterChangeDialog.open()
                            }
                            else {
                                base.setMetaDataEntry("approximate_diameter", old_approximate_diameter, new_approximate_diameter);
                                base.setMetaDataEntry("properties/diameter", properties.diameter, modified_value);
                            }
                        }

                        onValueTextChanged: updateCostPerMeter()
                    }
                }

                Row
                {
                    height: parent.rowHeight
                    spacing: UM.Theme.getSize("narrow_margin").width
                    UM.Label
                    {
                        height: informationPage.rowHeight
                        width: informationPage.columnWidth
                        text: catalog.i18nc("@label", "Filament Cost")
                    }

                    Cura.NumericTextFieldWithUnit
                    {
                        id: spoolCostTextField
                        valueText: base.getMaterialPreferenceValue(properties.guid, "spool_cost")
                        controlWidth: informationPage.columnWidth
                        controlHeight: informationPage.rowHeight
                        spacing: 0
                        unitText: base.currency
                        decimals: 2
                        maximum: 100000000

                        editingFinishedFunction: function()
                        {
                            var modified_text = valueText.replace(",", ".");
                            base.setMaterialPreferenceValue(properties.guid, "spool_cost", modified_text);
                        }

                        onValueTextChanged: updateCostPerMeter()
                    }
                }

                Row
                {
                    height: parent.rowHeight
                    spacing: UM.Theme.getSize("narrow_margin").width
                    UM.Label
                    {
                        height: informationPage.rowHeight
                        width: informationPage.columnWidth
                        text: catalog.i18nc("@label", "Filament weight")
                    }

                    Cura.NumericTextFieldWithUnit
                    {
                        id: spoolWeightTextField
                        valueText: base.getMaterialPreferenceValue(properties.guid, "spool_weight", Cura.ContainerManager.getContainerMetaDataEntry(properties.container_id, "properties/weight"))
                        controlWidth: informationPage.columnWidth
                        controlHeight: informationPage.rowHeight
                        spacing: 0
                        unitText: " g"
                        decimals: 0
                        maximum: 10000

                        editingFinishedFunction: function()
                        {
                            var modified_text = valueText.replace(",", ".")
                            base.setMaterialPreferenceValue(properties.guid, "spool_weight", modified_text)
                        }

                        onValueTextChanged: updateCostPerMeter()
                    }
                }

                Row
                {
                    height: parent.rowHeight
                    spacing: UM.Theme.getSize("narrow_margin").width
                    UM.Label
                    {
                        height: informationPage.rowHeight
                        width: informationPage.columnWidth
                        text: catalog.i18nc("@label", "Filament length")
                    }
                    UM.Label
                    {
                        width: informationPage.columnWidth
                        text: "~ %1 m".arg(Math.round(base.spoolLength))
                        height: informationPage.rowHeight
                    }
                }

                Row
                {
                    height: parent.rowHeight
                    spacing: UM.Theme.getSize("narrow_margin").width
                    UM.Label
                    {
                        height: informationPage.rowHeight
                        width: informationPage.columnWidth
                        text: catalog.i18nc("@label", "Cost per Meter")
                    }
                    UM.Label
                    {
                        height: informationPage.rowHeight
                        width: informationPage.columnWidth
                        text: "~ %1 %2/m".arg(base.costPerMeter.toFixed(2)).arg(base.currency)
                    }
                }

                UM.Label
                {
                    height: parent.rowHeight
                    width: informationPage.width
                    text: catalog.i18nc("@label", "This material is linked to %1 and shares some of its properties.").arg(base.linkedMaterialNames)
                    wrapMode: Text.WordWrap
                    visible: unlinkMaterialButton.visible
                }
                Cura.SecondaryButton
                {
                    id: unlinkMaterialButton
                    text: catalog.i18nc("@label", "Unlink Material")
                    visible: base.linkedMaterialNames != ""
                    onClicked:
                    {
                        Cura.ContainerManager.unlinkMaterial(base.currentMaterialNode)
                        base.reevaluateLinkedMaterials = true
                    }
                }

                UM.Label
                {
                    width: informationPage.width
                    height: parent.rowHeight
                    text: catalog.i18nc("@label", "Description")
                }
                Cura.ReadOnlyTextArea
                {
                    text: properties.description
                    width: informationPage.width - scrollBar.width
                    height: 0.4 * informationPage.width
                    wrapMode: Text.WordWrap

                    readOnly: !base.editingEnabled

                    onEditingFinished: base.setMetaDataEntry("description", properties.description, text)
                }

                UM.Label
                {
                    width: informationPage.width
                    height: parent.rowHeight
                    text: catalog.i18nc("@label", "Adhesion Information")
                }

                Cura.ReadOnlyTextArea
                {
                    text: properties.adhesion_info
                    width: informationPage.width - scrollBar.width
                    height: 0.4 * informationPage.width
                    wrapMode: Text.WordWrap
                    readOnly: !base.editingEnabled

                    onEditingFinished: base.setMetaDataEntry("adhesion_info", properties.adhesion_info, text)
                }
            }
        }

        ListView
        {
            id: settingsPage
            visible: pageSelectorTabRow.currentItem.activeView === "settings"
            clip: true

            anchors
            {
                fill: parent
                topMargin: UM.Theme.getSize("thin_margin").height
                bottomMargin: UM.Theme.getSize("thin_margin").height
                leftMargin: UM.Theme.getSize("thin_margin").width
                rightMargin: UM.Theme.getSize("thin_margin").width
            }

            width: settingsPage.width
            spacing: UM.Theme.getSize("narrow_margin").height

            ScrollBar.vertical: UM.ScrollBar
            {
                id: settingScrollBar
                parent: settingsPage.parent
                anchors
                {
                    top: parent.top
                    right: parent.right
                    bottom: parent.bottom
                }
            }

            property real columnWidth: Math.floor((width - settingScrollBar.width - UM.Theme.getSize("narrow_margin").width) / 2)

            model: UM.SettingDefinitionsModel
            {
                containerId: Cura.MachineManager.activeMachine != null ? Cura.MachineManager.activeMachine.definition.id: ""
                visibilityHandler: Cura.MaterialSettingsVisibilityHandler { }
                expanded: ["*"]
            }

            delegate: UM.TooltipArea
            {
                width: childrenRect.width
                height: childrenRect.height

                UM.TooltipArea
                {
                    anchors.fill: parent
                    text: model.description
                }
                UM.Label
                {
                    id: label
                    width: settingsPage.columnWidth
                    height: spinBox.height + UM.Theme.getSize("default_lining").height
                    text: model.label
                    elide: Text.ElideRight
                    verticalAlignment: Qt.AlignVCenter
                }
                Cura.NumericTextFieldWithUnit
                {
                    id: spinBox
                    anchors.left: label.right
                    valueText:
                    {
                        // In case the setting is not in the material...
                        if (!isNaN(parseFloat(materialPropertyProvider.properties.value)))
                        {
                            return parseFloat(materialPropertyProvider.properties.value);
                        }
                        // ... we search in the variant, and if it is not there...
                        if (!isNaN(parseFloat(variantPropertyProvider.properties.value)))
                        {
                            return parseFloat(variantPropertyProvider.properties.value);
                        }
                        // ... then look in the definition container.
                        if (!isNaN(parseFloat(machinePropertyProvider.properties.value)))
                        {
                            return parseFloat(machinePropertyProvider.properties.value);
                        }
                        return 0;
                    }
                    width: settingsPage.columnWidth
                    maximum: 99999
                    unitText: model.unit
                    decimals: model.unit == "mm" ? 2 : 0
                    enabled: base.editingEnabled

                    editingFinishedFunction: function()
                    {
                        materialPropertyProvider.setPropertyValue("value", parseFloat(valueText.replace(",", ".")))
                    }
                }

                UM.ContainerPropertyProvider
                {
                    id: materialPropertyProvider
                    containerId: base.containerId
                    watchedProperties: [ "value" ]
                    key: model.key
                }
                UM.ContainerPropertyProvider
                {
                    id: variantPropertyProvider
                    containerId: Cura.MachineManager.activeStack.variant.id
                    watchedProperties: [ "value" ]
                    key: model.key
                }
                UM.ContainerPropertyProvider
                {
                    id: machinePropertyProvider
                    containerId: Cura.MachineManager.activeMachine != null ? Cura.MachineManager.activeMachine.definition.id: ""
                    watchedProperties: ["value"]
                    key: model.key
                }
            }
        }
    }

    UM.TabRow
    {
        id: pageSelectorTabRow
        UM.TabRowButton
        {
            text: catalog.i18nc("@title", "Information")
            property string activeView: "information" //To determine which page gets displayed.
        }
        UM.TabRowButton
        {
            text: catalog.i18nc("@label", "Print settings")
            property string activeView: "settings"
        }
    }

    function updateCostPerMeter()
    {
        var modified_weight = spoolWeightTextField.valueText.replace(",", ".")
        var modified_cost = spoolCostTextField.valueText.replace(",", ".")
        var modified_diameter = diameterTextField.valueText.replace(",", ".")
        var modified_density = densityTextField.valueText.replace(",", ".")
        base.spoolLength = calculateSpoolLength(modified_diameter, modified_density, parseInt(modified_weight));
        base.costPerMeter = calculateCostPerMeter(parseFloat(modified_cost));
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
            spoolWeight = base.getMaterialPreferenceValue(properties.guid, "spool_weight", Cura.ContainerManager.getContainerMetaDataEntry(properties.container_id, "properties/weight"));
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
        if (old_value != new_value)
        {
            Cura.ContainerManager.setContainerMetaDataEntry(base.currentMaterialNode, entry_name, new_value)
            // make sure the UI properties are updated as well since we don't re-fetch the entire model here
            // When the entry_name is something like properties/diameter, we take the last part of the entry_name
            var list = entry_name.split("/")
            var key = list[list.length - 1]
            properties[key] = new_value
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
            return;
        }
        if (entry_name in materialPreferenceValues[material_guid] && new_value.toString() == 0)
        {
            // no need to store a 0, that's the default, so remove it
            materialPreferenceValues[material_guid].delete(entry_name);
            if (!(materialPreferenceValues[material_guid]))
            {
                // remove empty map
                materialPreferenceValues.delete(material_guid);
            }
        }
        if (new_value.toString() != 0)
        {
            // store new value
            materialPreferenceValues[material_guid][entry_name] = new_value;
        }

        // store preference
        UM.Preferences.setValue("cura/material_settings", JSON.stringify(materialPreferenceValues));
    }

    function getMaterialPreferenceValue(material_guid, entry_name, default_value)
    {
        if(material_guid in materialPreferenceValues && entry_name in materialPreferenceValues[material_guid])
        {
            return materialPreferenceValues[material_guid][entry_name];
        }
        default_value = default_value | 0;
        return default_value;
    }

    // update the display name of the material
    function updateMaterialDisplayName(old_name, new_name)
    {
        // don't change when new name is the same
        if (old_name == new_name)
        {
            return
        }

        // update the values
        base.materialManagementModel.setMaterialName(base.currentMaterialNode, new_name)
        properties.name = new_name
    }

    // update the type of the material
    function updateMaterialType(old_type, new_type)
    {
        base.setMetaDataEntry("material", old_type, new_type)
        properties.material = new_type
    }

    // update the brand of the material
    function updateMaterialBrand(old_brand, new_brand)
    {
        base.setMetaDataEntry("brand", old_brand, new_brand)
        properties.brand = new_brand
    }
}
