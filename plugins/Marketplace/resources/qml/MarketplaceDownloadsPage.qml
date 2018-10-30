// Copyright (c) 2018 Ultimaker B.V.
// Marketplace is released under the terms of the LGPLv3 or higher.

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

        MarketplaceDownloadsShowcase
        {
            id: showcase
            width: parent.width
        }

        MarketplaceDownloadsGrid
        {
            id: allPlugins
            width: parent.width
            heading: marketplace.viewCategory == "material" ? catalog.i18nc("@label", "Community Contributions") : catalog.i18nc("@label", "Community Plugins")
            model: marketplace.viewCategory == "material" ? marketplace.materialsAvailableModel : marketplace.pluginsAvailableModel
        }

        MarketplaceDownloadsGrid
        {
            id: genericMaterials
            visible: marketplace.viewCategory == "material"
            width: parent.width
            heading: catalog.i18nc("@label", "Generic Materials")
            model: marketplace.materialsGenericModel
        }
    }
}
