// Copyright (c) 2022 UltiMaker
// Cura is released under the terms of the LGPLv3 or higher.

import UM 1.4 as UM

Packages
{
    pageTitle: catalog.i18nc("@header", "Install Plugins")

    bannerVisible: UM.Preferences.getValue("cura/market_place_show_plugin_banner")
    bannerIcon: UM.Theme.getIcon("Shop")
    bannerText: catalog.i18nc("@text", "Streamline your workflow and customize your UltiMaker Cura experience with plugins contributed by our amazing community of users.")
    bannerReadMoreUrl: "https://support.ultimaker.com/hc/en-us/articles/360011968360/?utm_source=cura&utm_medium=software&utm_campaign=marketplace-learn-plugins"
    onRemoveBanner: function() {
        UM.Preferences.setValue("cura/market_place_show_plugin_banner", false)
        bannerVisible = false;
    }
    searchInBrowserUrl: "https://marketplace.ultimaker.com/app/cura/plugins?utm_source=cura&utm_medium=software&utm_campaign=marketplace-search-plugins-browser"
    showUpdateButton: true
    showInstallButton: true

    model: manager.PluginPackageList
}
