// Copyright (c) 2021 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import Marketplace 1.0 as Marketplace
import UM 1.4 as UM

Packages
{
    pageTitle: catalog.i18nc("@header", "Install Plugins")

    bannerVisible: UM.Preferences.getValue("cura/market_place_show_plugin_banner")
    bannerIcon: UM.Theme.getIcon("Shop")
    bannerText: catalog.i18nc("@text", "Streamline your workflow and customize your Ultimaker Cura experience with plugins contributed by our amazing community of users.")
    bannerReadMoreUrl: "" // TODO add when support page is ready
    onRemoveBanner: function() {
        UM.Preferences.setValue("cura/market_place_show_plugin_banner", false)
        bannerVisible = false;
    }

    model: Marketplace.RemotePackageList
    {
        packageTypeFilter: "plugin"
    }
}
