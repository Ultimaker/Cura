// Copyright (c) 2026 UltiMaker
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.4
import QtQuick.Layouts 2.7

import UM 1.5 as UM
import Cura 1.7 as Cura

Cura.Menu
{
    id: materialBrandMenu

    property var materialTypesModel
    title: materialTypesModel.name

    Instantiator
    {
        id: materialTypeInstantiator
        model: materialTypesModel.material_types

        delegate: Cura.Menu
        {
            title: model.name
            id: materialTypeMenu

            Repeater
            {
                model: colors

                delegate: Cura.MenuItem
                {
                    text: model.name

                    onTriggered: {
                        Cura.MachineManager.setMaterial(extruderIndex, model.container_node);
                    }
                }
            }
        }

        onObjectAdded: function(index, object)
        {
            materialBrandMenu.insertMenu(index, object);
            if (Qt.platform.os == "osx") object.title += " ";
        }
        onObjectRemoved: function(index, object) { materialBrandMenu.removeMenu(object); }
    }

}
