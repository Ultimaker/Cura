// Copyright (c) 2021 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import Marketplace 1.0 as Marketplace

Packages
{
    pageTitle: catalog.i18nc("@header", "Install Materials")

    bannerVisible: CuraApplication.shouldShowMarketPlaceMaterialBanner()
    bannerIcon: "Spool"
    bannerBody: catalog.i18nc("@text", "Streamline your workflow and customize your Ultimaker Cura experience with plugins contributed by our amazing community of users.")
    onRemoveBanner: function() {
        CuraApplication.closeMarketPlaceMaterialBanner();
        bannerVisible = false;
    }

    model: Marketplace.RemotePackageList
    {
        packageTypeFilter: "material"
    }
}
