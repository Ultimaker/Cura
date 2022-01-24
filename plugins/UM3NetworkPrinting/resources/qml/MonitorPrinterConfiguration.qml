// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 2.0
import UM 1.3 as UM

/**
 * The MonitorPrinterConfiguration accepts 2 configuration objects as input and
 * applies them to a MonitorBuildplateConfiguration instance and two instances
 * of MonitorExtruderConfiguration. It's used in both the MonitorPrintJobCard
 * component as well as the MonitorPrinterCard component.
 */
Item
{
    id: base

    // Extracted buildplate configuration
    property alias buildplate: buildplateConfig.buildplate

    // Array of extracted extruder configurations
    property var configurations: [null,null]

    // Default size, but should be stretched to fill parent
    height: 72 * parent.height
    width: 450 * screenScaleFactor // TODO: Theme!

    Row
    {
        id: extruderConfigurationRow
        spacing: 18 * screenScaleFactor // TODO: Theme!

        Repeater
        {
            id: extruderConfigurationRepeater
            model: configurations

            MonitorExtruderConfiguration
            {
                color: modelData && modelData.activeMaterial ? modelData.activeMaterial.color : UM.Theme.getColor("monitor_skeleton_loading")
                material: modelData && modelData.activeMaterial ? modelData.activeMaterial.name : ""
                position: modelData && typeof(modelData.position) === "number" ? modelData.position : -1 // Use negative one to create empty extruder number
                printCore: modelData ? modelData.hotendID : ""

                // Keep things responsive!
                width: Math.floor((base.width - (configurations.length - 1) * extruderConfigurationRow.spacing) / configurations.length)
            }

        }
    }

    MonitorBuildplateConfiguration
    {
        id: buildplateConfig
        anchors.bottom: parent.bottom
        buildplate: null
    }
}
