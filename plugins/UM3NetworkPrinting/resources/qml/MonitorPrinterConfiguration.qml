// Copyright (c) 2018 Ultimaker B.V.
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

    // Extracted extruder configuration for position 0
    property var config0: null

    // Extracted extruder configuration for position 1
    property var config1: null

    // Default size, but should be stretched to fill parent
    height: 72 * parent.height
    width: 450 * screenScaleFactor // TODO: Theme!

    Row
    {
        spacing: 18 * screenScaleFactor // TODO: Theme!

        MonitorExtruderConfiguration
        {
            color: config0 && config0.activeMaterial ? config0.activeMaterial.color : "#eeeeee" // TODO: Theme!
            material: config0 && config0.activeMaterial ? config0.activeMaterial.name : ""
            position: config0.position
            printCore: config0 ? config0.hotendID : ""
            visible: config0

            // Keep things responsive!
            width: Math.floor((base.width - parent.spacing) / 2)
        }

        MonitorExtruderConfiguration
        {
            color: config1 && config1.activeMaterial ? config1.activeMaterial.color : "#eeeeee" // TODO: Theme!
            material: config1 && config1.activeMaterial ? config1.activeMaterial.name : ""
            position: config1.position
            printCore: config1 ? config1.hotendID : ""
            visible: config1

            // Keep things responsive!
            width: Math.floor((base.width - parent.spacing) / 2)
        }
    }

    MonitorBuildplateConfiguration
    {
        id: buildplateConfig
        anchors.bottom: parent.bottom
        buildplate: "Glass" // 'Glass' as a default
    }
}