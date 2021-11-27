// Copyright (c) 2021 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

import Marketplace 1.0 as Marketplace
import UM 1.4 as UM

Packages
{
    pageTitle: catalog.i18nc("@header", "Manage packages")

    bannerVisible: CuraApplication.shouldShowMarketPlaceManagePackagesBanner()
    bannerIcon: "ArrowDoubleCircleRight"
    bannerBody: catalog.i18nc("@text", "Manage your Ultimaker Cura plugins and material profiles here. Make sure to keep your plugins up to date and backup your setup regularly.")
    readMoreUrl: "" // TODO add when support page is ready
    onRemoveBanner: function() {
        CuraApplication.closeMarketPlaceManagePackagesBanner();
        bannerVisible = false;
    }

    model: Marketplace.LocalPackageList
    {
    }
}
