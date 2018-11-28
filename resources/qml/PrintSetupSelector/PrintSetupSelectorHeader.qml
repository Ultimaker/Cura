// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3

import UM 1.3 as UM
import Cura 1.0 as Cura

RowLayout
{
    Cura.IconWithText
    {
        source: UM.Theme.getIcon("category_layer_height")
        text: Cura.MachineManager.activeStack ? Cura.MachineManager.activeQualityOrQualityChangesName + " " + layerHeight.properties.value + "mm" : ""

        UM.SettingPropertyProvider
        {
            id: layerHeight
            containerStack: Cura.MachineManager.activeStack
            key: "layer_height"
            watchedProperties: ["value"]
        }
    }

    Cura.IconWithText
    {
        source: UM.Theme.getIcon("category_infill")
        text: Cura.MachineManager.activeStack ? parseInt(infillDensity.properties.value) + "%" : "0%"

        UM.SettingPropertyProvider
        {
            id: infillDensity
            containerStack: Cura.MachineManager.activeStack
            key: "infill_sparse_density"
            watchedProperties: ["value"]
        }
    }

    Cura.IconWithText
    {
        source: UM.Theme.getIcon("category_support")
        text: supportEnabled.properties.value == "True" ? enabledText : disabledText


        UM.SettingPropertyProvider
        {
            id: supportEnabled
            containerStack: Cura.MachineManager.activeMachine
            key: "support_enable"
            watchedProperties: ["value"]
        }
    }

    Cura.IconWithText
    {
        source: UM.Theme.getIcon("category_adhesion")
        text: platformAdhesionType.properties.value != "skirt" && platformAdhesionType.properties.value != "none" ? enabledText : disabledText

        UM.SettingPropertyProvider
        {
            id: platformAdhesionType
            containerStack: Cura.MachineManager.activeMachine
            key: "adhesion_type"
            watchedProperties: [ "value"]
        }
    }
}