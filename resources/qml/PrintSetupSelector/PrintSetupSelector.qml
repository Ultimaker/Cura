// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.0

import UM 1.3 as UM
import Cura 1.0 as Cura

Cura.ExpandableComponent
{
    id: base

    property bool hideSettings: PrintInformation.preSliced

    property string enabledText: catalog.i18nc("@label:Should be short", "On")
    property string disabledText: catalog.i18nc("@label:Should be short", "Off")

    // This widget doesn't show tooltips by itself. Instead it emits signals so others can do something with it.
    signal showTooltip(Item item, point location, string text)
    signal hideTooltip()

    iconSource: UM.Theme.getIcon("pencil")
    popupPadding: UM.Theme.getSize("default_lining").width
    popupSpacingY: UM.Theme.getSize("narrow_margin").width

    popupClosePolicy: Popup.CloseOnEscape

    UM.I18nCatalog
    {
        id: catalog
        name: "cura"
    }

    Timer
    {
        id: tooltipDelayTimer
        interval: 500
        repeat: false
        property var item
        property string text

        onTriggered: base.showTooltip(base, {x: 0, y: item.y}, text)
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