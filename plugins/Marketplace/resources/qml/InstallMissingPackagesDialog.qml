// Copyright (c) 2021 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Window 2.2

import UM 1.5 as UM
import Cura 1.6 as Cura

Marketplace
{
    modality: Qt.ApplicationModal
    title: catalog.i18nc("@title", "Install missing packages")
    pageContentsSource: "MissingPackages.qml"
    showSearchHeader: false
    showOnboadBanner: false

    onClosing: manager.showMissingMaterialsWarning()
}
