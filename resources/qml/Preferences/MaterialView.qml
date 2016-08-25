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
    property string currency: UM.Preferences.getValue("general/currency") ? UM.Preferences.getValue("general/currency") : "€"
    property real firstColumnWidth: width * 0.45
    property real secondColumnWidth: width * 0.45
    property string containerId: ""

    Tab
    {
        title: "Information"
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
                    width: base.secondColumnWidth;
                    value: properties.density;
                    decimals: 2
                    suffix: "g/cm"
                    stepSize: 0.01
                    readOnly: !base.editingEnabled;

                    onEditingFinished: base.setMetaDataEntry("properties/density", properties.density, value)
                }

                Label { width: base.firstColumnWidth; height: parent.rowHeight; verticalAlignment: Qt.AlignVCenter; text: catalog.i18nc("@label", "Diameter") }
                ReadOnlySpinBox
                {
                    width: base.secondColumnWidth;
                    value: properties.diameter;
                    decimals: 2
                    suffix: "mm³"
                    stepSize: 0.01
                    readOnly: !base.editingEnabled;

                    onEditingFinished: base.setMetaDataEntry("properties/diameter", properties.diameter, value)
                }

                Label { width: base.firstColumnWidth; height: parent.rowHeight; verticalAlignment: Qt.AlignVCenter; text: catalog.i18nc("@label", "Filament Cost") }
                SpinBox
                {
                    width: base.secondColumnWidth;
                    value: properties.spool_cost;
                    prefix: base.currency
                    enabled: false
                }

                Label { width: base.firstColumnWidth; height: parent.rowHeight; verticalAlignment: Qt.AlignVCenter; text: catalog.i18nc("@label", "Filament weight") }
                SpinBox
                {
                    width: base.secondColumnWidth;
                    value: properties.spool_weight;
                    suffix: "g";
                    stepSize: 10
                    enabled: false
                }

                Label { width: base.firstColumnWidth; height: parent.rowHeight; verticalAlignment: Qt.AlignVCenter; text: catalog.i18nc("@label", "Filament length") }
                SpinBox
                {
                    width: base.secondColumnWidth;
                    value: parseFloat(properties.spool_length);
                    suffix: "m";
                    enabled: false
                }

                Label { width: base.firstColumnWidth; height: parent.rowHeight; verticalAlignment: Qt.AlignVCenter; text: catalog.i18nc("@label", "Cost per Meter (Approx.)") }
                SpinBox
                {
                    width: base.secondColumnWidth;
                    value: parseFloat(properties.cost_per_meter);
                    suffix: catalog.i18nc("@label", "%1/m".arg(base.currency));
                    enabled: false
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

    // Tiny convenience function to check if a value really changed before trying to set it.
    function setMetaDataEntry(entry_name, old_value, new_value)
    {
        if(old_value != new_value)
        {
            Cura.ContainerManager.setContainerMetaDataEntry(base.containerId, entry_name, new_value);
        }
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
