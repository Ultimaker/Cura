// Copyright (c) 2016 Ultimaker B.V.
// Uranium is released under the terms of the AGPLv3 or higher.

import QtQuick 2.1
import QtQuick.Controls 1.1
import QtQuick.Dialogs 1.2

import UM 1.2 as UM
import Cura 1.0 as Cura

TabView
{
    id: base

    property QtObject properties;

    property bool editingEnabled;

    property string currency: UM.Preferences.getValue("general/currency") ? UM.Preferences.getValue("general/currency") : "€"

    Tab
    {
        title: "Information"

        ScrollView
        {
            anchors.fill: parent
            anchors.margins: UM.Theme.getSize("default_margin").width

            Flow
            {
                id: containerGrid

                width: base.width - UM.Theme.getSize("default_margin").width * 4;

                property real firstColumnWidth: width * 0.5
                property real secondColumnWidth: width * 0.4

                property real rowHeight: textField.height;

                Label { width: parent.firstColumnWidth; height: parent.rowHeight; verticalAlignment: Qt.AlignVCenter; text: catalog.i18nc("@label", "Brand") }
                TextField { id: textField; width: parent.secondColumnWidth; text: properties.supplier; readOnly: !base.editingEnabled; }

                Label { width: parent.firstColumnWidth; height: parent.rowHeight; verticalAlignment: Qt.AlignVCenter; text: catalog.i18nc("@label", "Material Type") }
                TextField { width: parent.secondColumnWidth; text: properties.material_type; readOnly: !base.editingEnabled; }

                Label { width: parent.firstColumnWidth; height: parent.rowHeight; verticalAlignment: Qt.AlignVCenter; text: catalog.i18nc("@label", "Color") }

                Row
                {
                    width: parent.secondColumnWidth;
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
                    TextField { id: colorLabel; text: properties.color_name; readOnly: !base.editingEnabled }

                    ColorDialog { id: colorDialog; color: properties.color_code; onAccepted: colorSelector.color = color }
                }

                Item { width: parent.width; height: UM.Theme.getSize("default_margin").height }

                Label { width: parent.width; height: parent.rowHeight; verticalAlignment: Qt.AlignVCenter; text: "<b>" + catalog.i18nc("@label", "Properties") + "</b>" }

                Label { width: parent.firstColumnWidth; height: parent.rowHeight; verticalAlignment: Qt.AlignVCenter; text: catalog.i18nc("@label", "Density") }
                ReadOnlySpinBox
                {
                    width: parent.secondColumnWidth;
                    value: properties.density;
                    decimals: 2
                    suffix: "g/cm"
                    stepSize: 0.01
                    readOnly: !base.editingEnabled;
                }

                Label { width: parent.firstColumnWidth; height: parent.rowHeight; verticalAlignment: Qt.AlignVCenter; text: catalog.i18nc("@label", "Diameter") }
                ReadOnlySpinBox
                {
                    width: parent.secondColumnWidth;
                    value: properties.diameter;
                    decimals: 2
                    suffix: "mm³"
                    stepSize: 0.01
                    readOnly: !base.editingEnabled;
                }

                Label { width: parent.firstColumnWidth; height: parent.rowHeight; verticalAlignment: Qt.AlignVCenter; text: catalog.i18nc("@label", "Filament Cost") }
                ReadOnlySpinBox
                {
                    width: parent.secondColumnWidth;
                    value: properties.spool_cost;
                    prefix: base.currency
                    readOnly: !base.editingEnabled;
                }

                Label { width: parent.firstColumnWidth; height: parent.rowHeight; verticalAlignment: Qt.AlignVCenter; text: catalog.i18nc("@label", "Filament weight") }
                ReadOnlySpinBox
                {
                    width: parent.secondColumnWidth;
                    value: properties.spool_weight;
                    suffix: "g";
                    stepSize: 10
                    readOnly: !base.editingEnabled;
                }

                Label { width: parent.firstColumnWidth; height: parent.rowHeight; verticalAlignment: Qt.AlignVCenter; text: catalog.i18nc("@label", "Filament length") }
                ReadOnlySpinBox
                {
                    width: parent.secondColumnWidth;
                    value: parseFloat(properties.spool_length);
                    suffix: "m";
                    readOnly: !base.editingEnabled;
                }

                Label { width: parent.firstColumnWidth; height: parent.rowHeight; verticalAlignment: Qt.AlignVCenter; text: catalog.i18nc("@label", "Cost per Meter (Approx.)") }
                ReadOnlySpinBox
                {
                    width: parent.secondColumnWidth;
                    value: parseFloat(properties.cost_per_meter);
                    suffix: catalog.i18nc("@label", "%1/m".arg(base.currency));
                    readOnly: !base.editingEnabled;
                }

                Item { width: parent.width; height: UM.Theme.getSize("default_margin").height }

                Label { width: parent.width; height: parent.rowHeight; verticalAlignment: Qt.AlignVCenter; text: catalog.i18nc("@label", "Description") }

                TextArea
                {
                    text: properties.description;
                    width: parent.firstColumnWidth + parent.secondColumnWidth
                    wrapMode: Text.WordWrap

                    readOnly: !base.editingEnabled;
                }

                Label { width: parent.width; height: parent.rowHeight; verticalAlignment: Qt.AlignVCenter; text: catalog.i18nc("@label", "Adhesion Information") }

                TextArea
                {
                    text: properties.adhesion_info;
                    width: parent.firstColumnWidth + parent.secondColumnWidth
                    wrapMode: Text.WordWrap

                    readOnly: !base.editingEnabled;
                }
            }
        }
    }

    Tab
    {
        title: catalog.i18nc("@label", "Print settings")
        anchors.margins: UM.Theme.getSize("default_margin").height

        ScrollView
        {
            anchors.fill: parent;

            ListView
            {
                model: UM.SettingDefinitionsModel
                {
                    containerId: Cura.MachineManager.activeDefinitionId
                    visibilityHandler: UM.SettingPreferenceVisibilityHandler { }
                    expanded: ["*"]
                }

                delegate: Label { text: model.label }
            }
        }
    }
}
