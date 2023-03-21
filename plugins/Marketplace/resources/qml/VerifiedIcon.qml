// Copyright (c) 2022 UltiMaker
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.1

import UM 1.6 as UM
import Cura 1.6 as Cura
Control
{
    implicitWidth: UM.Theme.getSize("card_tiny_icon").width
    implicitHeight: UM.Theme.getSize("card_tiny_icon").height

    UM.ToolTip
    {
        tooltipText:
        {
            switch(packageData.packageType)
            {
                case "plugin": return catalog.i18nc("@info", "UltiMaker Verified Plug-in");
                case "material": return catalog.i18nc("@info", "UltiMaker Certified Material");
                default: return catalog.i18nc("@info", "UltiMaker Verified Package");
            }
        }
        visible: parent.hovered
        targetPoint: Qt.point(0, Math.round(parent.y + parent.height / 4))
    }

    Rectangle
    {
        anchors.fill: parent
        color: UM.Theme.getColor("action_button_hovered")
        radius: width
        UM.ColorImage
        {
            anchors.fill: parent
            color: UM.Theme.getColor("primary")
            source: packageData.packageType == "plugin" ? UM.Theme.getIcon("CheckCircle") : UM.Theme.getIcon("Certified")
        }
    }

    //NOTE: Can we link to something here? (Probably a static link explaining what verified is):
    // onClicked: Qt.openUrlExternally( XXXXXX )
}