// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 2.0
import UM 1.3 as UM

/**
 *
 */
Item
{
    id: base

    property var printJob: null
    property var config0: printJob ? printJob.configuration.extruderConfigurations[0] : null
    property var config1: printJob ? printJob.configuration.extruderConfigurations[1] : null

    height: 72 * screenScaleFactor // TODO: Theme!
    width: 450 * screenScaleFactor // TODO: Theme!

    Row
    {
        spacing: 18 * screenScaleFactor // TODO: Theme!

        MonitorExtruderConfiguration
        {
            color: config0 ? config0.activeMaterial.color : "#eeeeee" // TODO: Theme!
            material: config0 ? config0.activeMaterial.name : ""
            position: config0.position
            printCore: config0 ? config0.hotendID : ""
            visible: config0

            // Keep things responsive!
            width: Math.floor((base.width - parent.spacing) / 2)
        }

        MonitorExtruderConfiguration
        {
            color: config1 ? config1.activeMaterial.color : "#eeeeee" // TODO: Theme!
            material: config1 ? config1.activeMaterial.name : ""
            position: config1.position
            printCore: config1 ? config1.hotendID : ""
            visible: config1

            // Keep things responsive!
            width: Math.floor((base.width - parent.spacing) / 2)
        }
    }

    MonitorBuildplateConfiguration
    {
        anchors.bottom: parent.bottom
        buildplate: "Glass"
    }
}