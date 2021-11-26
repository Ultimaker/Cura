// Copyright (c) 2021 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import Marketplace 1.0 as Marketplace

Packages
{
    pageTitle: catalog.i18nc("@header", "Install Plugins")

    bannerVisible: CuraApplication.shouldShowMarketPlacePluginBanner()
    bannerIcon: "Shop"
    bannerBody: catalog.i18nc("@text", "Select and install material profiles optimised for your Ultimaker 3D printers.")
    onRemoveBanner: function() {
        CuraApplication.closeMarketPlacePluginBanner();
        bannerVisible = false;
    }

    model: Marketplace.RemotePackageList
    {
        packageTypeFilter: "plugin"
    }
}
