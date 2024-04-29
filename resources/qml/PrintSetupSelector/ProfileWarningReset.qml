// Copyright (C) 2022 UltiMaker
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10

import UM 1.6 as UM
import Cura 1.6 as Cura

import "../Dialogs"

Item
{
    property bool fullWarning: true  // <- Can you see the warning icon and the text, or is it just the buttons?
    property var simpleModeSettingsManager :CuraApplication.getSimpleModeSettingsManager()
    height: visible ? UM.Theme.getSize("action_button_icon").height : 0
    width: visible ? childrenRect.width: 0
    visible: Cura.MachineManager.hasUserSettings || (fullWarning && Cura.MachineManager.hasCustomQuality)

    Rectangle
    {
        id: warningIcon
        visible: fullWarning
        color: UM.Theme.getColor("warning")
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
            id: warningIconImage
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
            leftMargin: visible ? UM.Theme.getSize("thin_margin").width : 0
        }

        wrapMode: Text.WordWrap

        states: [
            State
            {
                name: "settings changed and custom quality"
                when: Cura.MachineManager.hasUserSettings && Cura.MachineManager.hasCustomQuality
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
                name: "recommended settings changed"
                when: Cura.MachineManager.hasUserSettings
                PropertyChanges
                {
                    target: warning
                    text:
                    {
                        var profile_name = Cura.MachineManager.activeQualityOrQualityChangesName;
                        return catalog.i18nc("@info %1 is the name of a profile", "Recommended settings (for <b>%1</b>) were altered.").arg(profile_name);
                    }
                }
            },
            State
            {
                name: "custom settings changed"
                when: simpleModeSettingsManager.isProfileCustomized
                PropertyChanges
                {
                    target: warning
                    text:
                    {
                        var profile_name = Cura.MachineManager.activeQualityOrQualityChangesName;
                        return catalog.i18nc("@info %1 is the name of a profile", "Some setting-values defined in <b>%1</b> were overridden.").arg(profile_name);
                    }
                }
            }
        ]
    }

    UM.SimpleButton
    {
        id: resetToDefaultQualityButton
        height: UM.Theme.getSize("action_button_icon").height
        width: visible ? height : 0
        iconSource: UM.Theme.getIcon("ArrowReset")
        anchors
        {
            right: buttonsSpacer.left
            verticalCenter: parent.verticalCenter
        }

        visible: enabled
        color: enabled ? UM.Theme.getColor("accent_1") : UM.Theme.getColor("disabled")
        hoverColor: UM.Theme.getColor("primary_hover")

        enabled: (fullWarning && Cura.MachineManager.hasCustomQuality) || Cura.MachineManager.hasUserSettings
        onClicked: Cura.MachineManager.resetToUseDefaultQuality()

        UM.ToolTip
        {
            visible: parent.hovered
            y: parent.y + parent.height + UM.Theme.getSize("default_margin").height
            targetPoint: Qt.point(parent.x, Math.round(parent.y + parent.height / 2))
            tooltipText: catalog.i18nc("@info", "Reset to defaults.")
        }
    }

    // Spacer
    Item
    {
        id: buttonsSpacer
        width: compareAndSaveButton.visible ? UM.Theme.getSize("default_margin").width : 0
        anchors.right: compareAndSaveButton.left
    }

    UM.SimpleButton
    {
        id: compareAndSaveButton
        height: UM.Theme.getSize("action_button_icon").height
        width: visible ? height : 0
        iconSource: UM.Theme.getIcon("Save")
        anchors
        {
            right: parent.right
            verticalCenter: parent.verticalCenter
        }

        visible: enabled
        color: enabled ? UM.Theme.getColor("accent_1") : UM.Theme.getColor("disabled")
        hoverColor: UM.Theme.getColor("primary_hover")

        enabled: Cura.MachineManager.hasUserSettings
        onClicked: CuraApplication.showCompareAndSaveProfileChanges
            (
                Cura.MachineManager.hasCustomQuality ?
                DiscardOrKeepProfileChangesDialog.ButtonsType.SaveFromCustom :
                DiscardOrKeepProfileChangesDialog.ButtonsType.SaveFromBuiltIn
            )

        UM.ToolTip
        {
            visible: parent.hovered
            y: parent.y + parent.height + UM.Theme.getSize("default_margin").height
            targetPoint: Qt.point(parent.x, Math.round(parent.y + parent.height / 2))
            tooltipText: catalog.i18nc("@info", "Compare and save.")
        }
    }
}
