// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 1.4

import UM 1.2 as UM
import Cura 1.6 as Cura

Menu
{
    id: menu
    title: "Intent"

    property int extruderIndex: 0

    Cura.IntentCategoryModel
    {
        id: intentCategoryModel
    }

    Instantiator
    {
        model: intentCategoryModel

        MenuItem //Section header.
        {
            text: model.name
            enabled: false
            checked: false

            property var per_category_intents: Cura.IntentModel
            {
                id: intentModel
                intentCategory: model.intent_category
            }

            property var intent_instantiator: Instantiator
            {
                model: intentModel
                MenuItem
                {
                    text: model.name
                    checkable: true
                    checked: false
                    Binding on checked
                    {
                        when: Cura.MachineManager.activeStack != null
                        value: Cura.MachineManager.activeStack.intent.metaData["intent_category"] == intentModel.intentCategory && Cura.MachineManager.activeStack.quality.metaData["quality_type"] == model.quality_type
                    }
                    exclusiveGroup: group
                    onTriggered: Cura.IntentManager.selectIntent(intentModel.intentCategory, model.quality_type)
                }

                onObjectAdded: menu.insertItem(index, object)
                onObjectRemoved: menu.removeItem(object)
            }
        }

        onObjectAdded: menu.insertItem(index, object)
        onObjectRemoved: menu.removeItem(object)
    }
    ExclusiveGroup { id: group }
}
