// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.15

import UM 1.5 as UM
import Cura 1.0 as Cura


//
// Infill
//
Item
{
    id: infillRow
    height: childrenRect.height

    property real labelColumnWidth: Math.round(width / 3)

    // Here are the elements that are shown in the left column
    Cura.IconWithText
    {
        id: infillRowTitle
        anchors.top: parent.top
        anchors.left: parent.left
        source: UM.Theme.getIcon("Infill1")
        text: `${catalog.i18nc("@label", "Infill")} (%)`
        font: UM.Theme.getFont("medium")
        width: labelColumnWidth
        iconSize: UM.Theme.getSize("medium_button_icon").width
        tooltipText: catalog.i18nc("@label", "Gradual infill will gradually increase the amount of infill towards the top.")
    }

    InfillSlider
    {
        id: infillSliderContainer
        height: childrenRect.height
    }

    //  Gradual Support Infill Checkbox
    UM.CheckBox
    {
        id: enableGradualInfillCheckBox
        property alias _hovered: enableGradualInfillMouseArea.containsMouse

        anchors.top: infillSliderContainer.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").height
        anchors.left: infillSliderContainer.left

        text: catalog.i18nc("@label", "Gradual infill")
        enabled: recommendedPrintSetup.settingsEnabled
        visible: infillSteps.properties.enabled == "True"
        checked: parseInt(infillSteps.properties.value) > 0

        MouseArea
        {
            id: enableGradualInfillMouseArea

            anchors.fill: parent
            hoverEnabled: true
            enabled: true

            property var previousInfillDensity: parseInt(infillDensity.properties.value)

            onClicked:
            {
                // Set to 90% only when enabling gradual infill
                var newInfillDensity;
                if (parseInt(infillSteps.properties.value) == 0)
                {
                    previousInfillDensity = parseInt(infillDensity.properties.value)
                    newInfillDensity = 90
                } else {
                    newInfillDensity = previousInfillDensity
                }
                Cura.MachineManager.setSettingForAllExtruders("infill_sparse_density", "value", String(newInfillDensity))

                var infill_steps_value = 0
                if (parseInt(infillSteps.properties.value) == 0)
                {
                    infill_steps_value = 5
                }

                Cura.MachineManager.setSettingForAllExtruders("gradual_infill_steps", "value", infill_steps_value)
            }

            onEntered: base.showTooltip(enableGradualInfillCheckBox, Qt.point(-infillSliderContainer.x - UM.Theme.getSize("thick_margin").width, 0),
                    catalog.i18nc("@label", "Gradual infill will gradually increase the amount of infill towards the top."))

            onExited: base.hideTooltip()
        }
    }

    UM.SettingPropertyProvider
    {
        id: infillDensity
        containerStackId: Cura.MachineManager.activeStackId
        key: "infill_sparse_density"
        watchedProperties: [ "value" ]
        storeIndex: 0
    }

    UM.SettingPropertyProvider
    {
        id: infillSteps
        containerStackId: Cura.MachineManager.activeStackId
        key: "gradual_infill_steps"
        watchedProperties: ["value", "enabled"]
        storeIndex: 0
    }
}
