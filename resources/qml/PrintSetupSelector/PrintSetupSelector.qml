// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.0

import UM 1.3 as UM
import Cura 1.0 as Cura

Cura.ExpandableComponent
{
    id: printSetupSelector

    property string enabledText: catalog.i18nc("@label:Should be short", "On")
    property string disabledText: catalog.i18nc("@label:Should be short", "Off")

    iconSource: UM.Theme.getIcon("pencil")
    popupPadding: UM.Theme.getSize("default_lining").width
    popupSpacingY: UM.Theme.getSize("narrow_margin").width

    popupClosePolicy: Popup.CloseOnEscape

    UM.I18nCatalog
    {
        id: catalog
        name: "cura"
    }

    headerItem: PrintSetupSelectorHeader
    {
        anchors.fill: parent
    }

    Cura.ExtrudersModel
    {
        id: extrudersModel
    }

    popupItem: PrintSetupSelectorContents {}
}