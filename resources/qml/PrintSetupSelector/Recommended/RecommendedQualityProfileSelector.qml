// Copyright (c) 2023 UltiMaker
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Layouts 2.10

import UM 1.5 as UM
import Cura 1.7 as Cura
import ".."

Item
{
    id: qualityRow

    property bool hasQualityOptions: true

    height: childrenRect.height
    visible: intentSelectionRepeater.count > 1 && hasQualityOptions //Only show selector if there's more options than just "default".

    RowLayout
    {
        id: intentRow
        width: parent.width

        Repeater
        {
            id: intentSelectionRepeater
            model: Cura.IntentSelectionModel {}

            RecommendedQualityProfileSelectorButton
            {
                profileName: model.name
                icon: model.icon ? model.icon : ""
                custom_icon: model.custom_icon ? model.custom_icon : ""
                tooltipText: model.description ? model.description : ""

                selected: Cura.MachineManager.activeIntentCategory == model.intent_category

                onClicked: {
                    var qualityType
                    if (Cura.MachineManager.intentCategoryHasQuality(model.intent_category, Cura.MachineManager.activeQualityType))
                    {
                        qualityType = Cura.MachineManager.activeQualityType
                    } else {
                        qualityType = Cura.MachineManager.getDefaultQualityTypeForIntent(model.intent_category)
                    }
                    Cura.IntentManager.selectIntent(model.intent_category, qualityType)
                }
            }
        }
    }
}
