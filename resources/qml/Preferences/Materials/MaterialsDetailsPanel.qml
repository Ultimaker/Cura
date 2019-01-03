// Copyright (c) 2018 Ultimaker B.V.
// Uranium is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.3
import QtQuick.Dialogs 1.2

import UM 1.2 as UM
import Cura 1.0 as Cura

Item
{
    id: detailsPanel

    property var currentItem: null

    onCurrentItemChanged:
    {
        // When the current item changes, the detail view needs to be updated
        if (currentItem != null)
        {
            updateMaterialPropertiesObject()
            materialDetailsView.currentMaterialNode = currentItem.container_node
        }
    }

    function updateMaterialPropertiesObject()
    {
        // DRAGON WARNING!!! DO NOT TOUCH THIS IF YOU DON'T KNOW.
        // TL;DR: Always update "container_id" first!
        //
        // Other widgets such as MaterialsView have bindings towards "materialProperties" and its properties. Here the
        // properties are updated one by one, and each change can trigger a reaction on those widgets that have
        // connections to the property gets changed, and some reactions will use functions such as
        // ContainerManager.getContainerMetaDataEntry() to fetch data using the "container_id" as the reference.
        // We need to change "container_id" first so any underlying triggers will use the correct "container_id" to
        // fetch data. Or, for example, if we change GUID first, which triggered the weight widget to fetch weight
        // before we can update "container_id", so it will fetch weight with the wrong (old) "container_id".
        materialProperties.container_id = currentItem.id

        materialProperties.name = currentItem.name || "Unknown"
        materialProperties.guid = currentItem.GUID
        materialProperties.brand = currentItem.brand || "Unknown"
        materialProperties.material = currentItem.material || "Unknown"
        materialProperties.color_name = currentItem.color_name || "Yellow"
        materialProperties.color_code = currentItem.color_code || "yellow"
        materialProperties.description = currentItem.description || ""
        materialProperties.adhesion_info = currentItem.adhesion_info || ""
        materialProperties.density = currentItem.density || 0.0
        materialProperties.diameter = currentItem.diameter || 0.0
        materialProperties.approximate_diameter = currentItem.approximate_diameter || "0"
    }

    Item
    {
        anchors.fill: parent

        Item    // Material title Label
        {
            id: profileName

            width: parent.width
            height: childrenRect.height

            Label {
                text: materialProperties.name
                font: UM.Theme.getFont("large_bold")
            }
        }

        MaterialsView    // Material detailed information view below the title Label
        {
            id: materialDetailsView
            anchors
            {
                left: parent.left
                right: parent.right
                top: profileName.bottom
                topMargin: UM.Theme.getSize("default_margin").height
                bottom: parent.bottom
            }

            editingEnabled: currentItem != null && !currentItem.is_read_only

            properties: materialProperties
            containerId: currentItem != null ? currentItem.id : ""
            currentMaterialNode: currentItem.container_node
        }

        QtObject
        {
            id: materialProperties

            property string guid: "00000000-0000-0000-0000-000000000000"
            property string container_id: "Unknown";
            property string name: "Unknown";
            property string profile_type: "Unknown";
            property string brand: "Unknown";
            property string material: "Unknown";  // This needs to be named as "material" to be consistent with
                                                    // the material container's metadata entry

            property string color_name: "Yellow";
            property color color_code: "yellow";

            property real density: 0.0;
            property real diameter: 0.0;
            property string approximate_diameter: "0";

            property real spool_cost: 0.0;
            property real spool_weight: 0.0;
            property real spool_length: 0.0;
            property real cost_per_meter: 0.0;

            property string description: "";
            property string adhesion_info: "";
        }
    }
}