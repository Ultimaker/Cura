// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.2 as UM
import Cura 1.6 as Cura

Item
{
    id: icon
    property var affected_extruders
    property var intent_type: ""

    implicitWidth: UM.Theme.getSize("section_icon").width
    implicitHeight: UM.Theme.getSize("section_icon").height

    UM.RecolorImage
    {
        source: UM.Theme.getIcon("Information")
        color: UM.Theme.getColor("icon")
        anchors.fill: parent
    }
    MouseArea
    {
        anchors.fill: parent
        hoverEnabled: parent.visible
        onEntered:
        {
            var tooltipContent = catalog.i18ncp("@label %1 is filled in with the type of a profile. %2 is filled with a list of numbers (eg '1' or '1, 2')", "There is no %1 profile for the configuration in extruder %2. The default intent will be used instead", "There is no %1 profile for the configurations in extruders %2. The default intent will be used instead", affected_extruders.length).arg(intent_type).arg(affected_extruders)
            base.showTooltip(icon.parent, Qt.point(-UM.Theme.getSize("thick_margin").width, 0),  tooltipContent)
        }
        onExited: base.hideTooltip()
    }
}
