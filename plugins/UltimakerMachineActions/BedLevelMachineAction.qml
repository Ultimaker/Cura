// Copyright (c) 2016 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

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

        Label
        {
            id: pageTitle
            width: parent.width
            text: catalog.i18nc("@title", "Build Plate Leveling")
            wrapMode: Text.WordWrap
            font.pointSize: 18;
        }
        Label
        {
            id: pageDescription
            anchors.top: pageTitle.bottom
            anchors.topMargin: UM.Theme.getSize("default_margin").height
            width: parent.width
            wrapMode: Text.WordWrap
            text: catalog.i18nc("@label", "To make sure your prints will come out great, you can now adjust your buildplate. When you click 'Move to Next Position' the nozzle will move to the different positions that can be adjusted.")
        }
        Label
        {
            id: bedlevelingText
            anchors.top: pageDescription.bottom
            anchors.topMargin: UM.Theme.getSize("default_margin").height
            width: parent.width
            wrapMode: Text.WordWrap
            text: catalog.i18nc("@label", "For every position; insert a piece of paper under the nozzle and adjust the print build plate height. The print build plate height is right when the paper is slightly gripped by the tip of the nozzle.")
        }

        Row
        {
            id: bedlevelingWrapper
            anchors.top: bedlevelingText.bottom
            anchors.topMargin: UM.Theme.getSize("default_margin").height
            anchors.horizontalCenter: parent.horizontalCenter
            width: childrenRect.width
            spacing: UM.Theme.getSize("default_margin").width

            Button
            {
                id: startBedLevelingButton
                text: catalog.i18nc("@action:button","Start Build Plate Leveling")
                onClicked:
                {
                    startBedLevelingButton.visible = false;
                    bedlevelingButton.visible = true;
                    manager.startBedLeveling();
                }
            }

            Button
            {
                id: bedlevelingButton
                text: catalog.i18nc("@action:button","Move to Next Position")
                visible: false
                onClicked:
                {
                    manager.moveToNextLevelPosition();
                }
            }
        }
    }
}
