// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 1.4
import QtQuick.Controls 2.3 as Controls2
import QtQuick.Controls.Styles 1.4

import UM 1.2 as UM
import Cura 1.6 as Cura
import ".."

Item
{
    id: qualityRow
    height: childrenRect.height

    property real labelColumnWidth: Math.round(width / 3)
    property real settingsColumnWidth: width - labelColumnWidth

    // Here are the elements that are shown in the left column

    Column
    {
        anchors
        {
            left: parent.left
            right: parent.right
        }

        spacing: UM.Theme.getSize("default_margin").height

        Controls2.ButtonGroup
        {
            id: activeProfileButtonGroup
            exclusive: true
            onClicked: Cura.IntentManager.selectIntent(button.modelData.intent_category, button.modelData.quality_type)
        }

        Item
        {
            height: childrenRect.height
            anchors
            {
                left: parent.left
                right: parent.right
            }
            Cura.IconWithText
            {
                id: profileLabel
                source: UM.Theme.getIcon("category_layer_height")
                text: catalog.i18nc("@label", "Profiles")
                font: UM.Theme.getFont("medium")
                width: labelColumnWidth
            }
            UM.SimpleButton
            {
                id: customisedSettings

                visible: Cura.SimpleModeSettingsManager.isProfileCustomized || Cura.MachineManager.hasCustomQuality
                height: visible ? UM.Theme.getSize("print_setup_icon").height : 0
                width: height
                anchors
                {
                    right: profileLabel.right
                    rightMargin: UM.Theme.getSize("default_margin").width
                    leftMargin: UM.Theme.getSize("default_margin").width
                    verticalCenter: parent.verticalCenter
                }

                color: hovered ? UM.Theme.getColor("setting_control_button_hover") : UM.Theme.getColor("setting_control_button")
                iconSource: UM.Theme.getIcon("reset")

                onClicked:
                {
                    // if the current profile is user-created, switch to a built-in quality
                    Cura.MachineManager.resetToUseDefaultQuality()
                }
                onEntered:
                {
                    var tooltipContent = catalog.i18nc("@tooltip","You have modified some profile settings. If you want to change these go to custom mode.")
                    base.showTooltip(qualityRow, Qt.point(-UM.Theme.getSize("thick_margin").width, 0),  tooltipContent)
                }
                onExited: base.hideTooltip()
            }

            Cura.LabelBar
            {
                id: labelbar
                anchors
                {
                    left: profileLabel.right
                    right: parent.right
                }

                model: Cura.QualityProfilesDropDownMenuModel
                modelKey: "layer_height"
            }
        }


        Repeater
        {
            model: Cura.IntentCategoryModel {}
            Item
            {
                anchors
                {
                    left: parent.left
                    right: parent.right
                }
                height: intentCategoryLabel.height

                Label
                {
                    id: intentCategoryLabel
                    text: model.name
                    width: labelColumnWidth - UM.Theme.getSize("section_icon").width
                    anchors.left: parent.left
                    anchors.leftMargin: UM.Theme.getSize("section_icon").width + UM.Theme.getSize("narrow_margin").width
                    font: UM.Theme.getFont("medium")
                    color: UM.Theme.getColor("text")
                    renderType: Text.NativeRendering
                    elide: Text.ElideRight
                }

                NoIntentIcon
                {
                    affected_extruders: Cura.MachineManager.extruderPositionsWithNonActiveIntent
                    intent_type: model.name
                    anchors.right: intentCategoryLabel.right
                    anchors.rightMargin: UM.Theme.getSize("narrow_margin").width
                    width: intentCategoryLabel.height * 0.75
                    anchors.verticalCenter: parent.verticalCenter
                    height: width
                    visible: Cura.MachineManager.activeIntentCategory == model.intent_category && affected_extruders.length
                }

                Cura.RadioCheckbar
                {
                    anchors
                    {
                        left: intentCategoryLabel.right
                        right: parent.right
                    }
                    dataModel: model["qualities"]
                    buttonGroup: activeProfileButtonGroup

                    function checkedFunction(modelItem)
                    {
                        if(Cura.MachineManager.hasCustomQuality)
                        {
                            // When user created profile is active, no quality tickbox should be active.
                            return false
                        }

                        if(modelItem === null)
                        {
                            return false
                        }
                        return Cura.MachineManager.activeQualityType == modelItem.quality_type && Cura.MachineManager.activeIntentCategory == modelItem.intent_category
                    }

                    isCheckedFunction: checkedFunction
                }

                MouseArea // tooltip hover area
                {
                    anchors.fill: parent
                    hoverEnabled: true
                    enabled: model.description !== undefined
                    acceptedButtons: Qt.NoButton // react to hover only, don't steal clicks

                    onEntered:
                    {
                        base.showTooltip(
                            intentCategoryLabel,
                            Qt.point(-(intentCategoryLabel.x - qualityRow.x) - UM.Theme.getSize("thick_margin").width, 0),
                            model.description
                        )
                    }
                    onExited: base.hideTooltip()
                }
            }

        }
    }
}