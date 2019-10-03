// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3

import UM 1.3 as UM
import Cura 1.0 as Cura

RowLayout
{
    property string enabledText: catalog.i18nc("@label:Should be short", "On")
    property string disabledText: catalog.i18nc("@label:Should be short", "Off")

    Cura.IconWithText
    {
        source: UM.Theme.getIcon("category_layer_height")
        text:
        {
            if (Cura.MachineManager.activeStack)
            {
                var text = Cura.MachineManager.activeQualityOrQualityChangesName

                // If this is a custom quality, add intent (if present) and quality it is based on
                if (Cura.MachineManager.isActiveQualityCustom)
                {
                    if (Cura.MachineManager.activeIntentName != "")
                    {
                        text += " - " + Cura.MachineManager.activeIntentName
                    }
                    text += " - " + Cura.MachineManager.activeQualityName
                }

                if (!Cura.MachineManager.hasNotSupportedQuality)
                {
                    text += " - " + layerHeight.properties.value + "mm"
                    text += Cura.MachineManager.isActiveQualityExperimental ? " - " + catalog.i18nc("@label", "Experimental") : ""
                }
                return text
            }
            return ""
        }
        font: UM.Theme.getFont("medium")

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
        font: UM.Theme.getFont("medium")

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
        font: UM.Theme.getFont("medium")

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
        font: UM.Theme.getFont("medium")

        UM.SettingPropertyProvider
        {
            id: platformAdhesionType
            containerStack: Cura.MachineManager.activeMachine
            key: "adhesion_type"
            watchedProperties: [ "value"]
        }
    }
}