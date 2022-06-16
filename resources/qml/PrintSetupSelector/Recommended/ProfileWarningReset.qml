import QtQuick 2.10

import UM 1.6 as UM
import Cura 1.6 as Cura

Item
{
    height: visible ? UM.Theme.getSize("action_button_icon").height : 0
    visible: Cura.SimpleModeSettingsManager.isProfileCustomized || Cura.MachineManager.hasCustomQuality

    Rectangle
    {
        id: warningIcon
        color: UM.Theme.getColor("um_yellow_5")
        height: UM.Theme.getSize("action_button_icon").height
        width: height
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
        width: parent.width - warningIcon.width - resetToDefaultQualityButton.width
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
                        return "<b>%1</b> %2".arg(profile_name).arg(catalog.i18nc("@info", "custom profile is active and you overwrote some settings."))
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
                        return "<b>%1</b> %2".arg(profile_name).arg(catalog.i18nc("@info", "custom profile is overriding some settings."))
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
            right: parent.right
            verticalCenter: parent.verticalCenter
        }

        color: UM.Theme.getColor("accent_1")

        onClicked:
        {
            Cura.MachineManager.resetToUseDefaultQuality()
        }
    }

}