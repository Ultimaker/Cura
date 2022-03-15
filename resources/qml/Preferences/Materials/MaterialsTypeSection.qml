// Copyright (c) 2022 Ultimaker B.V.
// Uranium is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.3

import UM 1.5 as UM
import Cura 1.0 as Cura

Column
{
    id: material_type_section
    property var materialType: null
    property string materialBrand: materialType !== null ? materialType.brand : ""
    property string materialName: materialType !== null ? materialType.name : ""
    property bool expanded: materialList.expandedTypes.indexOf(`${materialBrand}_${materialName}`) !== -1
    property var colorsModel: materialType !== null ? materialType.colors : null
    property alias indented: categoryButton.indented
    width: parent.width

    Cura.CategoryButton
    {
        id: categoryButton
        width: parent.width
        height: UM.Theme.getSize("preferences_page_list_item").height
        labelText: materialName
        labelFont: UM.Theme.getFont("default")
        expanded: material_type_section.expanded
        onClicked:
        {
            const identifier = `${materialBrand}_${materialName}`;
            const i = materialList.expandedTypes.indexOf(identifier);
            if (i !== -1)
            {
                materialList.expandedTypes.splice(i, 1); // remove
            }
            else
            {
                materialList.expandedTypes.push(identifier); // add
            }
            UM.Preferences.setValue("cura/expanded_types", materialList.expandedTypes.join(";"));
        }
    }

    Column
    {
        visible: material_type_section.expanded
        width: parent.width

        Repeater
        {
            model: colorsModel
            delegate: MaterialsSlot
            {
                material: model
            }
        }
    }

    Connections
    {
        target: UM.Preferences
        function onPreferenceChanged(preference)
        {
            if (preference !== "cura/expanded_types" && preference !== "cura/expanded_brands")
            {
                return;
            }

            material_type_section.expanded = materialList.expandedTypes.indexOf(`${materialBrand}_${materialName}`) !== -1;
        }
    }
}
