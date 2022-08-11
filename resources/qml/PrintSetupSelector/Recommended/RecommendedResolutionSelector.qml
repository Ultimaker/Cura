// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10

import UM 1.6 as UM
import Cura 1.7 as Cura

Item
{
    id: recommendedResolutionSelector
    height: childrenRect.height

    property real labelColumnWidth: Math.round(width / 3)
    property string _previousResolution: ""  //Internal variable to detect changes.
    Component.onCompleted: _previousResolution = Cura.MachineManager.activeQualityType;

    visible: visibilityPreset.count > 0 //Only show if there are quality types to select from.

    Cura.IconWithText
    {
        id: resolutionTitle
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.leftMargin: - UM.Theme.getSize("thick_lining").width
        source: UM.Theme.getIcon("PrintQuality")
        text: catalog.i18nc("@label", "Resolution")
        width: labelColumnWidth
        height: parent.height
        spacing: UM.Theme.getSize("thick_margin").width
        iconSize: UM.Theme.getSize("medium_button_icon").width
    }

    Cura.ComboBox
    {
        id: visibilityPreset
        implicitHeight: UM.Theme.getSize("combobox").height
        implicitWidth: UM.Theme.getSize("combobox").width
        anchors
        {
            top: parent.top
            right: parent.right
        }

        textRole: "display_text"
        textFormat: Text.StyledText

        model: Cura.ActiveIntentQualitiesModel{}

        currentIndex:
        {
            var current_quality_type = Cura.MachineManager.activeQualityType

            var index = 0
            for (var i = 0; i < model.count; i++)
            {
                if (model.getItem(i).quality_type == current_quality_type)
                {
                    index = i
                    break
                }
            }
            return index
        }

        onActivated:
        {
            var selected_item = model.getItem(currentIndex)
            Cura.IntentManager.selectIntent(selected_item.intent_category, selected_item.quality_type)

            if (Cura.IntentManager.currentIntentCategory == selected_item.intent_category)
            {
                recommendedResolutionSelector._previousResolution = selected_item.quality_type;
            }
        }

        Connections
        {
            target: Cura.IntentManager
            function onIntentCategoryChanged()
            {
                if(recommendedResolutionSelector._previousResolution !== Cura.MachineManager.activeQualityType)
                {
                    visibilityPreset.pulse();
                }
                recommendedResolutionSelector._previousResolution = Cura.MachineManager.activeQualityType;
            }
        }
    }
}