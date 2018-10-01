// Copyright (c) 2018 Ultimaker B.V.
// Toolbox is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import UM 1.1 as UM

ScrollView
{
    frameVisible: false
    width: parent.width
    height: parent.height
    style: UM.Theme.styles.scrollview

    flickableItem.flickableDirection: Flickable.VerticalFlick

    Column
    {
        width: base.width
        spacing: UM.Theme.getSize("default_margin").height
        height: childrenRect.height

        ToolboxDownloadsShowcase
        {
            id: showcase
            width: parent.width
        }

        ToolboxDownloadsGrid
        {
            id: allPlugins
            width: parent.width
            heading: toolbox.viewCategory == "material" ? catalog.i18nc("@label", "Community Contributions") : catalog.i18nc("@label", "Community Plugins")
            model: toolbox.viewCategory == "material" ? toolbox.materialsAvailableModel : toolbox.pluginsAvailableModel
        }

        ToolboxDownloadsGrid
        {
            id: genericMaterials
            visible: toolbox.viewCategory == "material"
            width: parent.width
            heading: catalog.i18nc("@label", "Generic Materials")
            model: toolbox.materialsGenericModel
        }
    }
}
