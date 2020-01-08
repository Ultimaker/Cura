// Copyright (c) 2019 Ultimaker B.V.
// Toolbox is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.1 as UM
import Cura 1.1 as Cura

import "../components"

Cura.ScrollView
{
    clip: true
    width: parent.width
    height: parent.height
    contentHeight: mainColumn.height

    Column
    {
        id: mainColumn
        width: base.width
        spacing: UM.Theme.getSize("default_margin").height

        ToolboxDownloadsShowcase
        {
            id: showcase
            width: parent.width
        }

        ToolboxDownloadsGrid
        {
            id: allPlugins
            width: parent.width
            heading: toolbox.viewCategory === "material" ? catalog.i18nc("@label", "Community Contributions") : catalog.i18nc("@label", "Community Plugins")
            model: toolbox.viewCategory === "material" ? toolbox.materialsAvailableModel : toolbox.pluginsAvailableModel
        }

        ToolboxDownloadsGrid
        {
            id: genericMaterials
            visible: toolbox.viewCategory === "material"
            width: parent.width
            heading: catalog.i18nc("@label", "Generic Materials")
            model: toolbox.materialsGenericModel
        }
    }
}
