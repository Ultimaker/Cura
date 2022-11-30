//Copyright (C) 2022 UltiMaker B.V.
//Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10

import UM 1.6 as UM
import Cura 1.6 as Cura

Item
{
    property bool fullWarning: true  // <- Can you see the warning icon and the text, or is it just the buttons?

    height: visible ? UM.Theme.getSize("action_button_icon").height : 0
    visible: Cura.SimpleModeSettingsManager.isProfileCustomized || Cura.MachineManager.hasCustomQuality

    Rectangle
    {
        id: warningIcon
        visible: fullWarning
        color: UM.Theme.getColor("um_yellow_5")
        height: UM.Theme.getSize("action_button_icon").height
        width: visible ? height : 0
        radius: width
        anchors
        {
            left: parent.left
            verticalCenter: parent.verticalCenter
        }
        UM.ColorImage
        {
            height: UM.Theme.getSize("action_button_icon").height
            width: height
            source: UM.Theme.getIcon("Warning", "low")
        }
    }

    UM.Label
    {
        id: warning
        visible: fullWarning
        width: visible ? parent.width - warningIcon.width - (compareAndSaveButton.width + resetToDefaultQualityButton.width) : 0
        anchors
        {
            left: warningIcon.right
            verticalCenter: parent.verticalCenter
            leftMargin: UM.Theme.getSize("thin_margin").width
        }

        wrapMode: Text.WordWrap

        states: [
            State
            {
                name: "settings changed and custom quality"
                when: Cura.SimpleModeSettingsManager.isProfileCustomized && Cura.MachineManager.hasCustomQuality
                PropertyChanges
                {
                    target: warning
                    text: {
                        var profile_name = Cura.MachineManager.activeQualityChangesGroup.name
                        return catalog.i18nc("@info, %1 is the name of the custom profile", "<b>%1</b> custom profile is active and you overwrote some settings.").arg(profile_name)
                    }
                }

            },
            State
            {
                name: "custom quality"
                when: Cura.MachineManager.hasCustomQuality
                PropertyChanges
                {
                    target: warning
                    text: {
                        var profile_name = Cura.MachineManager.activeQualityChangesGroup.name
                        return catalog.i18nc("@info, %1 is the name of the custom profile", "<b>%1</b> custom profile is overriding some settings.").arg(profile_name)
                    }
                }
            },
            State
            {
                name: "settings changed"
                when: Cura.SimpleModeSettingsManager.isProfileCustomized
                PropertyChanges
                {
                    target: warning
                    text: catalog.i18nc("@info", "Some settings were changed.")
                }
            }
        ]
    }

    UM.SimpleButton
    {
        id: resetToDefaultQualityButton
        height: UM.Theme.getSize("action_button_icon").height
        width: height
        iconSource: UM.Theme.getIcon("ArrowReset")
        anchors
        {
            right: buttonsSpacer.left
            verticalCenter: parent.verticalCenter
        }

        color: enabled ? UM.Theme.getColor("accent_1") : UM.Theme.getColor("disabled")
        hoverColor: UM.Theme.getColor("primary_hover")

        enabled: Cura.MachineManager.hasCustomQuality || Cura.SimpleModeSettingsManager.isProfileCustomized
        onClicked: Cura.MachineManager.resetToUseDefaultQuality()

        UM.ToolTip
        {
            visible: parent.hovered
            targetPoint: Qt.point(parent.x - width, Math.round(parent.y + parent.height / 2))
            tooltipText: catalog.i18nc("@info", "Reset to defaults.")
        }
    }

    // Spacer
    Item
    {
        id: buttonsSpacer
        width:  UM.Theme.getSize("action_button_icon").height
        anchors.right: compareAndSaveButton.left
    }

    UM.SimpleButton
    {
        id: compareAndSaveButton
        height: UM.Theme.getSize("action_button_icon").height
        width: height
        iconSource: UM.Theme.getIcon("Save")
        anchors
        {
            right: parent.right
            verticalCenter: parent.verticalCenter
        }

        color: enabled ? UM.Theme.getColor("accent_1") : UM.Theme.getColor("disabled")
        hoverColor: UM.Theme.getColor("primary_hover")

        enabled: Cura.SimpleModeSettingsManager.isProfileCustomized
        onClicked: CuraApplication.showCompareAndSaveProfileChanges(Cura.MachineManager.hasCustomQuality ? "saveFromCustom" : "saveFromBuiltIn")

        UM.ToolTip
        {
            visible: parent.hovered
            targetPoint: Qt.point(parent.x - width, Math.round(parent.y + parent.height / 2))
            tooltipText: catalog.i18nc("@info", "Compare and safe.")
        }
    }
}
