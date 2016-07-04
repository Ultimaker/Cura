// Copyright (c) 2016 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1
import QtQuick.Window 2.1

import UM 1.2 as UM
import Cura 1.0 as Cura


Cura.MachineAction
{
    anchors.fill: parent;
    Item
    {
        id: bedLevelMachineAction
        anchors.fill: parent;

        UM.I18nCatalog { id: catalog; name: "cura"; }
        Column
        {
            anchors.fill: parent;
            Label
            {
                width: parent.width
                wrapMode: Text.WordWrap
                text: catalog.i18nc("@label","Please select any upgrades made to this ultimaker original");
            }
            CheckBox
            {
                text: catalog.i18nc("@label", "Self-built heated bed")
                checked: manager.hasHeatedBed
                onClicked: manager.hasHeatedBed ? manager.removeHeatedBed() : manager.addHeatedBed()
            }
        }
    }
}