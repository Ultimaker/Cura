// Copyright (c) 2022 UltiMaker
// Cura is released under the terms of the LGPLv3 or higher.

import UM 1.4 as UM

Packages
{
    pageTitle: catalog.i18nc("@header", "Install Materials")

    bannerVisible:  UM.Preferences.getValue("cura/market_place_show_material_banner")
    bannerIcon: UM.Theme.getIcon("Spool")
    bannerText: catalog.i18nc("@text", "Select and install material profiles optimised for your UltiMaker 3D printers.")
    bannerReadMoreUrl: "https://support.ultimaker.com/hc/en-us/articles/360011968360/?utm_source=cura&utm_medium=software&utm_campaign=marketplace-learn-materials"
    onRemoveBanner: function() {
        UM.Preferences.setValue("cura/market_place_show_material_banner", false);
        bannerVisible = false;
    }
    searchInBrowserUrl: "https://marketplace.ultimaker.com/app/cura/materials?utm_source=cura&utm_medium=software&utm_campaign=marketplace-search-materials-browser"
    showUpdateButton: true
    showInstallButton: true

    model: manager.MaterialPackageList
}
