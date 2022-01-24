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
        source: UM.Theme.getIcon("Sliders", "medium")
        iconSize: UM.Theme.getSize("button_icon").width
        text:
        {
            if (Cura.MachineManager.activeStack)
            {
                var resultMap = Cura.MachineManager.activeQualityDisplayNameMap
                var text = resultMap["main"]
                if (resultMap["suffix"])
                {
                    text += " - " + resultMap["suffix"]
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
        elide: Text.ElideMiddle

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
        source: UM.Theme.getIcon("Infill1")
        text: Cura.MachineManager.activeStack ? parseInt(infillDensity.properties.value) + "%" : "0%"
        font: UM.Theme.getFont("medium")
        iconSize: UM.Theme.getSize("medium_button_icon").width

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
        source: UM.Theme.getIcon("Support")
        text: supportEnabled.properties.value == "True" ? enabledText : disabledText
        font: UM.Theme.getFont("medium")
        iconSize: UM.Theme.getSize("medium_button_icon").width

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
        source: UM.Theme.getIcon("Adhesion")
        text: platformAdhesionType.properties.value != "skirt" && platformAdhesionType.properties.value != "none" ? enabledText : disabledText
        font: UM.Theme.getFont("medium")
        iconSize: UM.Theme.getSize("medium_button_icon").width

        UM.SettingPropertyProvider
        {
            id: platformAdhesionType
            containerStack: Cura.MachineManager.activeMachine
            key: "adhesion_type"
            watchedProperties: [ "value"]
        }
    }
}
