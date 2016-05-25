// Copyright (c) 2016 Ultimaker B.V.
// Uranium is released under the terms of the AGPLv3 or higher.

import QtQuick 2.1
import QtQuick.Controls 1.1
import QtQuick.Dialogs 1.2

import UM 1.2 as UM
import Cura 1.0 as Cura

UM.ManagementPage
{
    id: base;

    title: catalog.i18nc("@title:tab", "Materials");

    model: UM.InstanceContainersModel { filter: { "type": "material", "definition": Cura.MachineManager.activeDefinitionId } }
/*
    onAddObject: { var selectedMaterial = UM.MaterialManager.createProfile(); base.selectMaterial(selectedMaterial); }
    onRemoveObject: confirmDialog.open();
    onRenameObject: { renameDialog.open(); renameDialog.selectText(); }
*/
//     activateEnabled: false
    addEnabled: false
    removeEnabled: false
    renameEnabled: false

    scrollviewCaption: " "
    detailsVisible: true

    property string currency: UM.Preferences.getValue("general/currency")

    Item {
        UM.I18nCatalog { id: catalog; name: "cura"; }

        visible: base.currentItem != null
        anchors.fill: parent

        Label { id: profileName; text: materialProperties.name; font: UM.Theme.getFont("large"); width: parent.width; }

        TabView {
            id: scrollView
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: profileName.bottom
            anchors.topMargin: UM.Theme.getSize("default_margin").height
            anchors.bottom: parent.bottom

            Tab {
                title: "Information"
                anchors.margins: UM.Theme.getSize("default_margin").height

                Flow {
                    id: containerGrid

                    width: scrollView.width;
                    property real columnWidth: width / 2

                    Label { width: parent.columnWidth; text: catalog.i18nc("@label", "Profile Type") }
                    Label { width: parent.columnWidth; text: materialProperties.profile_type }

                    Label { width: parent.columnWidth; text: catalog.i18nc("@label", "Supplier") }
                    Label { width: parent.columnWidth; text: materialProperties.supplier }

                    Label { width: parent.columnWidth; text: catalog.i18nc("@label", "Material Type") }
                    Label { width: parent.columnWidth; text: materialProperties.material_type }

                    Label { width: parent.columnWidth; text: catalog.i18nc("@label", "Color") }

                    Row {
                        width: parent.columnWidth;
                        spacing: UM.Theme.getSize("default_margin").width/2
                        Rectangle {
                            color: materialProperties.color_code
                            width: colorLabel.height
                            height: colorLabel.height
                            border.width: UM.Theme.getSize("default_lining").height
                        }
                        Label { id: colorLabel; text: materialProperties.color_name }
                    }

                    Item { width: parent.width; height: UM.Theme.getSize("default_margin").height }

                    Label { width: parent.width; text: "<b>" + catalog.i18nc("@label", "Properties") + "</b>" }

                    Label { width: parent.columnWidth; text: catalog.i18nc("@label", "Density") }
                    Label { width: parent.columnWidth; text: materialProperties.density }

                    Label { width: parent.columnWidth; text: catalog.i18nc("@label", "Diameter") }
                    Label { width: parent.columnWidth; text: materialProperties.diameter }

                    Label {
                        text: catalog.i18nc("@label", "Filament cost")
                        width: parent.columnWidth;
                        height: spoolCostInput.height
                        verticalAlignment: Text.AlignVCenter
                    }

                    Row {
                        width: parent.columnWidth;
                        Label {
                            text: base.currency ? base.currency + " " : " "
                            anchors.verticalCenter: parent.verticalCenter
                        }
                        TextField {
                            id: spoolCostInput
                            text: materialProperties.spool_cost
                        }
                    }

                    Label { width: parent.columnWidth; text: catalog.i18nc("@label", "Filament weight") }
                    Label { width: parent.columnWidth; text: materialProperties.spool_weight + " " + "g" }

                    Label { width: parent.columnWidth; text: catalog.i18nc("@label", "Filament length") }
                    Label { width: parent.columnWidth; text: materialProperties.spool_length + " " + "m" }

                    Label { width: parent.columnWidth; text: catalog.i18nc("@label", "Cost per meter") }
                    Label { width: parent.columnWidth; text: catalog.i18nc("@label", "approx. %1 %2/m").arg(materialProperties.cost_per_meter).arg(base.currency); }

                    Item { width: parent.width; height: UM.Theme.getSize("default_margin").height }

                    Label {
                        text: materialProperties.description ? "<b>" + catalog.i18nc("@label", "Information") + "</b><br>" + materialProperties.description : "";
                        width: parent.width
                        wrapMode: Text.WordWrap
                    }
                    Label {
                        text: materialProperties.adhesion_info ? "<b>" + catalog.i18nc("@label", "Adhesion") + "</b><br>" + materialProperties.adhesion_info : "";
                        width: parent.width
                        wrapMode: Text.WordWrap
                    }
                }
            }
            Tab {
                title: catalog.i18nc("@label", "Print settings")
                anchors.margins: UM.Theme.getSize("default_margin").height

                Grid {
                    columns: 2
                    spacing: UM.Theme.getSize("default_margin").width

                    Column {
                        Repeater {
                            model: base.currentItem ? base.currentItem.settings : null
                            Label {
                                text: modelData.name.toString();
                                elide: Text.ElideMiddle;
                            }
                        }
                    }
                    Column {
                        Repeater {
                            model: base.currentItem ? base.currentItem.settings : null
                            Label { text: modelData.value.toString() + " " + modelData.unit.toString(); }
                        }
                    }
                }
            }
        }

        QtObject
        {
            id: materialProperties

            property string name: "Unknown";
            property string profile_type: "Unknown";
            property string supplier: "Unknown";
            property string material_type: "Unknown";

            property string color_name: "Yellow";
            property color color_code: "yellow";

            property string density: "Unknown";
            property string diameter: "Unknown";

            property string spool_cost: "Unknown";
            property string spool_weight: "Unknown";
            property string spool_length: "Unknown";
            property string cost_per_meter: "Unknown";

            property string description: "";
            property string adhesion_info: "";
        }
    }

    onCurrentItemChanged:
    {
        if(!currentItem == null)
        {
            return
        }

        materialProperties.name = currentItem.name;

        if(currentItem.metadata != undefined && currentItem.metadata != null)
        {
            materialProperties.supplier = currentItem.metadata.brand ? currentItem.metadata.brand : "Unknown";
            materialProperties.material_type = currentItem.metadata.material ? currentItem.metadata.material : "Unknown";
            materialProperties.color_name = currentItem.metadata.color_name ? currentItem.metadata.color_name : "Yellow";
            materialProperties.color_code = currentItem.metadata.color_code ? currentItem.metadata.color_code : "yellow";

            materialProperties.description = currentItem.metadata.description ? currentItem.metadata.description : "";
            materialProperties.adhesion_info = currentItem.metadata.adhesion_info ? currentItem.metadata.adhesion_info : "";

            if(currentItem.metadata.properties != undefined && currentItem.metadata.properties != null)
            {
                materialProperties.density = currentItem.metadata.properties.density ? currentItem.metadata.properties.density : "Unknown";
                materialProperties.diameter = currentItem.metadata.properties.diameter ? currentItem.metadata.properties.diameter : "Unknown";
            }
            else
            {
                materialProperties.density = "Unknown";
                materialProperties.diameter = "Unknown";
            }
        }
    }
}
