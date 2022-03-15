// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.3

import UM 1.5 as UM
import Cura 1.0 as Cura

// An expandable list of materials. Includes both the header (this file) and the items (brandMaterialList)

Column
{
    id: brand_section

    property string sectionName: ""
    property var elementsModel   // This can be a MaterialTypesModel or GenericMaterialsModel or FavoriteMaterialsModel
    property bool hasMaterialTypes: true  // It indicates whether it has material types or not
    property bool expanded: materialList.expandedBrands.indexOf(sectionName) !== -1
    width: parent.width

    Cura.CategoryButton
    {
        width: parent.width
        labelText: sectionName
        labelFont: UM.Theme.getFont("medium_bold")
        expanded: brand_section.expanded
        onClicked:
        {
            const i = materialList.expandedBrands.indexOf(sectionName);
            if (i !== -1)
            {
                materialList.expandedBrands.splice(i, 1); // remove
            }
            else
            {
                materialList.expandedBrands.push(sectionName); // add
            }
            UM.Preferences.setValue("cura/expanded_brands", materialList.expandedBrands.join(";"));
        }
    }

    Column
    {
        id: brandMaterialList
        width: parent.width
        visible: brand_section.expanded

        Repeater
        {
            model: elementsModel

            delegate: Loader
            {
                width: parent.width
                property var element: model
                sourceComponent: hasMaterialTypes ? materialsTypeSection : materialSlot
            }
        }
    }

    Component
    {
        id: materialsTypeSection
        MaterialsTypeSection
        {
            materialType: element
            indented: true
        }
    }

    Component
    {
        id: materialSlot
        MaterialsSlot
        {
            material: element
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

            brand_section.expanded = materialList.expandedBrands.indexOf(sectionName) !== -1;
        }
    }
}
