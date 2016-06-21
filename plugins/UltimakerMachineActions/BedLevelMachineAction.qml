// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1
import QtQuick.Window 2.1

import UM 1.2 as UM
import Cura 1.0 as Cura


// The action items always need to be wrapped in a component.
Component
{
    Item
    {
        id: wizardPage
        anchors.fill: parent;

        UM.I18nCatalog { id: catalog; name: "cura"; }

        Label
        {
            id: pageTitle
            width: parent.width
            text: catalog.i18nc("@title", "Bed Leveling")
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
            text: catalog.i18nc("@label", "For every position; insert a piece of paper under the nozzle and adjust the print bed height. The print bed height is right when the paper is slightly gripped by the tip of the nozzle.")
        }

        Item
        {
            id: bedlevelingWrapper
            anchors.top: bedlevelingText.bottom
            anchors.topMargin: UM.Theme.getSize("default_margin").height
            anchors.horizontalCenter: parent.horizontalCenter
            height: skipBedlevelingButton.height
            width: bedlevelingButton.width + skipBedlevelingButton.width + UM.Theme.getSize("default_margin").height < wizardPage.width ? bedlevelingButton.width + skipBedlevelingButton.width + UM.Theme.getSize("default_margin").height : wizardPage.width
            Button
            {
                id: bedlevelingButton
                anchors.top: parent.top
                anchors.left: parent.left
                text: catalog.i18nc("@action:button","Move to Next Position");
                onClicked:
                {
                    manager.moveToNextLevelPosition()
                }
            }

            Button
            {
                id: skipBedlevelingButton
                anchors.top: parent.width < wizardPage.width ? parent.top : bedlevelingButton.bottom
                anchors.topMargin: parent.width < wizardPage.width ? 0 : UM.Theme.getSize("default_margin").height/2
                anchors.left: parent.width < wizardPage.width ? bedlevelingButton.right : parent.left
                anchors.leftMargin: parent.width < wizardPage.width ? UM.Theme.getSize("default_margin").width : 0
                text: catalog.i18nc("@action:button","Skip bed leveling");
                onClicked:
                {
                }
            }
        }
    }
}
