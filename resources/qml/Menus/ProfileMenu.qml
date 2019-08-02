// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 1.4

import UM 1.2 as UM
import Cura 1.0 as Cura

Menu
{
    id: menu

    MenuItem { action: Cura.Actions.addProfile }
    MenuItem { action: Cura.Actions.updateProfile }
    MenuItem { action: Cura.Actions.resetProfile }
    MenuSeparator { }
    MenuItem { action: Cura.Actions.manageProfiles }
    MenuSeparator { }

    Instantiator
    {
        model: Cura.QualityProfilesDropDownMenuModel

        MenuItem
        {
            text:
            {
                var full_text = (model.layer_height != "") ? model.name + " - " + model.layer_height + model.layer_height_unit : model.name
                full_text += model.is_experimental ? " - " + catalog.i18nc("@label", "Experimental") : ""
                return full_text
            }
            checkable: true
            checked: Cura.MachineManager.activeQualityOrQualityChangesName == model.name
            exclusiveGroup: group
            onTriggered: Cura.MachineManager.setQualityGroup(model.quality_group)
            visible: model.available
        }

        onObjectAdded: menu.insertItem(index, object)
        onObjectRemoved: menu.removeItem(object)
    }

    MenuSeparator
    {
        id: customSeparator
        visible: Cura.CustomQualityProfilesDropDownMenuModel.count > 0
    }

    Instantiator
    {
        id: customProfileInstantiator
        model: Cura.CustomQualityProfilesDropDownMenuModel

        Connections
        {
            target: Cura.CustomQualityProfilesDropDownMenuModel
            onModelReset: customSeparator.visible = Cura.CustomQualityProfilesDropDownMenuModel.count > 0
        }

        MenuItem
        {
            text: model.name
            checkable: true
            checked: Cura.MachineManager.activeQualityOrQualityChangesName == model.name
            exclusiveGroup: group
            onTriggered: Cura.MachineManager.setQualityChangesGroup(model.quality_changes_group)
        }

        onObjectAdded:
        {
            customSeparator.visible = model.count > 0;
            menu.insertItem(index, object);
        }
        onObjectRemoved:
        {
            customSeparator.visible = model.count > 0;
            menu.removeItem(object);
        }
    }

    ExclusiveGroup { id: group; }
}
