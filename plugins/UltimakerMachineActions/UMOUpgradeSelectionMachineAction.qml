// Copyright (c) 2022 UltiMaker
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.5 as UM
import Cura 1.1 as Cura


Cura.MachineAction
{
    UM.I18nCatalog { id: catalog; name: "cura"; }
    anchors.fill: parent

    Item
    {
        id: upgradeSelectionMachineAction
        anchors.fill: parent
        anchors.topMargin: UM.Theme.getSize("default_margin").width * 5
        anchors.leftMargin: UM.Theme.getSize("default_margin").width * 4

        UM.Label
        {
            id: pageDescription
            anchors.top: parent.top
            anchors.topMargin: UM.Theme.getSize("default_margin").height
            width: parent.width
            wrapMode: Text.WordWrap
            text: catalog.i18nc("@label","Please select any upgrades made to this UltiMaker Original")
            font: UM.Theme.getFont("medium")
        }

        UM.CheckBox
        {
            anchors.top: pageDescription.bottom
            anchors.topMargin: UM.Theme.getSize("default_margin").height

            text: catalog.i18nc("@label", "Heated Build Plate (official kit or self-built)")
            checked: manager.hasHeatedBed
            onClicked: manager.setHeatedBed(checked)
        }
    }
}
