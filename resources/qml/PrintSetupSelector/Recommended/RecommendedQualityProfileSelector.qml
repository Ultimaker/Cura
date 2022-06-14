// Copyright (c) 2022 Ultimaker B.V.
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
    height: childrenRect.height

    RowLayout
    {
        id: intentRow
        width: parent.width

        Repeater
        {
            model: Cura.IntentSelectionModel {}

            RecommendedQualityProfileSelectorButton
            {
                profileName: model.name
                icon: model.icon


                selected: Cura.MachineManager.activeIntentCategory == model.intent_category

                onClicked: {
                    var qualityType
                    if (Cura.MachineManager.intentCategoryHasQuality(model.intent_category, Cura.MachineManager.activeQualityType))
                    {
                        qualityType = Cura.MachineManager.activeQualityType
                    } else {
                        qualityType = Cura.MachineManager.getDefaultQualityTypeForIntent(model.intent_category)
                        print(Cura.MachineManager.getDefaultQualityTypeForIntent(model.intent_category))
                    }
                    Cura.IntentManager.selectIntent(model.intent_category, qualityType)
                }
            }
        }
    }
}
