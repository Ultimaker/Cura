// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 1.4
import QtQuick.Controls 2.3 as Controls2
import QtQuick.Controls.Styles 1.4

import UM 1.2 as UM
import Cura 1.6 as Cura

Item
{
    id: qualityRow
    height: childrenRect.height

    property real labelColumnWidth: Math.round(width / 3)
    property real settingsColumnWidth: width - labelColumnWidth

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
            text: catalog.i18nc("@label", "Profiles")
            font: UM.Theme.getFont("medium")
            anchors.left: parent.left
            anchors.right: customisedSettings.left
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