// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3

import UM 1.3 as UM
import Cura 1.1 as Cura


Cura.MachineAction
{
    UM.I18nCatalog { id: catalog; name: "cura"; }

    anchors.fill: parent

    Item
    {
        id: bedLevelMachineAction
        anchors.top: parent.top
        anchors.topMargin: UM.Theme.getSize("default_margin").height * 3
        anchors.horizontalCenter: parent.horizontalCenter
        width: parent.width * 3 / 4

        Label
        {
            id: pageTitle
            width: parent.width
            text: catalog.i18nc("@title", "Build Plate Leveling")
            wrapMode: Text.WordWrap
            font: UM.Theme.getFont("medium")
            color: UM.Theme.getColor("text")
            renderType: Text.NativeRendering
        }

        Label
        {
            id: pageDescription
            anchors.top: pageTitle.bottom
            anchors.topMargin: UM.Theme.getSize("default_margin").height * 3
            width: parent.width
            wrapMode: Text.WordWrap
            text: catalog.i18nc("@label", "To make sure your prints will come out great, you can now adjust your buildplate. When you click 'Move to Next Position' the nozzle will move to the different positions that can be adjusted.")
            font: UM.Theme.getFont("default")
            color: UM.Theme.getColor("text")
            renderType: Text.NativeRendering
        }

        Label
        {
            id: bedlevelingText
            anchors.top: pageDescription.bottom
            anchors.topMargin: UM.Theme.getSize("default_margin").height
            width: parent.width
            wrapMode: Text.WordWrap
            text: catalog.i18nc("@label", "For every position; insert a piece of paper under the nozzle and adjust the print build plate height. The print build plate height is right when the paper is slightly gripped by the tip of the nozzle.")
            font: UM.Theme.getFont("default")
            color: UM.Theme.getColor("text")
            renderType: Text.NativeRendering
        }

        Row
        {
            id: bedlevelingWrapper
            anchors.top: bedlevelingText.bottom
            anchors.topMargin: UM.Theme.getSize("default_margin").height * 3
            anchors.horizontalCenter: parent.horizontalCenter
            width: childrenRect.width
            spacing: UM.Theme.getSize("default_margin").width

            Cura.ActionButton
            {
                id: startBedLevelingButton
                text: catalog.i18nc("@action:button", "Start Build Plate Leveling")
                onClicked:
                {
                    startBedLevelingButton.visible = false
                    bedlevelingButton.visible = true
                    manager.startBedLeveling()
                }
            }

            Cura.ActionButton
            {
                id: bedlevelingButton
                text: catalog.i18nc("@action:button", "Move to Next Position")
                visible: false
                onClicked:
                {
                    manager.moveToNextLevelPosition()
                }
            }
        }
    }
}
