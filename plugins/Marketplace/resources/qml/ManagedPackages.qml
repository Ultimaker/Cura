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
    bannerType: "__MANAGE_PACKAGES__"
    model: Marketplace.LocalPackageList
    {
    }
}
