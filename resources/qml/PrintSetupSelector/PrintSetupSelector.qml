// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.0

import UM 1.3 as UM
import Cura 1.0 as Cura

Cura.ExpandableComponent
{
    id: printSetupSelector

    property bool preSlicedData: PrintInformation.preSliced

    contentPadding: UM.Theme.getSize("default_lining").width
    contentHeaderTitle: catalog.i18nc("@label", "Print settings")
    enabled: !preSlicedData

    UM.I18nCatalog
    {
        id: catalog
        name: "cura"
    }

    headerItem: PrintSetupSelectorHeader {}

    Cura.ExtrudersModel
    {
        id: extrudersModel
    }

    contentItem: PrintSetupSelectorContents {}
}