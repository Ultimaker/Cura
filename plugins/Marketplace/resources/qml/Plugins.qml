// Copyright (c) 2021 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import Marketplace 1.0 as Marketplace
import UM 1.4 as UM

Packages
{
    pageTitle: catalog.i18nc("@header", "Install Plugins")

    bannerVisible: UM.Preferences.getValue("cura/market_place_show_plugin_banner")
    bannerIcon: UM.Theme.getIcon("Shop")
    bannerText: catalog.i18nc("@text", "Select and install material profiles optimised for your Ultimaker 3D printers.")
    readMoreUrl: "" // TODO add when support page is ready
    onRemoveBanner: function() {
        UM.Preferences.setValue("cura/market_place_show_plugin_banner", false)
        bannerVisible = false;
    }

    model: Marketplace.RemotePackageList
    {
        packageTypeFilter: "plugin"
    }
}
