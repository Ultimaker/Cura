// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 1.4
import QtQuick.Controls 2.3 as Controls2
import QtQuick.Controls.Styles 1.4

import UM 1.2 as UM
import Cura 1.6 as Cura


//
// Quality profile
//
Item
{
    id: qualityRow
    height: childrenRect.height

    property real labelColumnWidth: Math.round(width / 3)
    property real settingsColumnWidth: width - labelColumnWidth

    Timer
    {
        id: qualitySliderChangeTimer
        interval: 50
        running: false
        repeat: false
        onTriggered:
        {
            var item = Cura.QualityProfilesDropDownMenuModel.getItem(qualitySlider.value);
            Cura.MachineManager.activeQualityGroup = item.quality_group;
        }
    }


    // Here are the elements that are shown in the left column
    Item
    {
        id: titleRow
        width: labelColumnWidth
        height: childrenRect.height

        Cura.IconWithText
        {
            id: qualityRowTitle
            source: UM.Theme.getIcon("category_layer_height")
            text: catalog.i18nc("@label", "Layer Height")
            font: UM.Theme.getFont("medium")
            anchors.left: parent.left
            anchors.right: customisedSettings.left
        }

        UM.SimpleButton
        {
            id: customisedSettings

            visible: Cura.SimpleModeSettingsManager.isProfileCustomized || Cura.MachineManager.hasCustomQuality
            height: visible ? UM.Theme.getSize("print_setup_icon").height : 0
            width: height
            anchors
            {
                right: parent.right
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
    }

    Column
    {
        anchors
        {
            left: titleRow.right
            right: parent.right
        }

        spacing: UM.Theme.getSize("default_margin").height

        Controls2.ButtonGroup
        {
            id: activeProfileButtonGroup
            exclusive: true
            onClicked: Cura.IntentManager.selectIntent(button.modelData.intent_category, button.modelData.quality_type)

        }

        Cura.LabelBar
        {
            id: labelbar
            anchors
            {
                left: parent.left
                right: parent.right
            }

            model: Cura.QualityProfilesDropDownMenuModel
            modelKey: "layer_height"
        }

        Repeater
        {
            model: Cura.IntentCategoryModel{}
            Cura.RadioCheckbar
            {
                anchors
                {
                    left: parent.left
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
                    return Cura.MachineManager.activeQualityType == modelItem.quality_type && Cura.MachineManager.activeIntentCategory == modelItem.intent_category
                }

                isCheckedFunction: checkedFunction
            }

        }
    }
}