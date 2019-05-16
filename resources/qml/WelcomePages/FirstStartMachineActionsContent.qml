// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.3 as UM
import Cura 1.1 as Cura


//
// This component contains the content for the "What's new in Ultimaker Cura" page of the welcome on-boarding process.
//
Item
{
    UM.I18nCatalog { id: catalog; name: "cura" }

    property var machineActionsModel: CuraApplication.getFirstStartMachineActionsModel()

    Component.onCompleted:
    {
        // Reset the action to start from the beginning when it is shown.
        machineActionsModel.reset()
    }

    // Go to the next page when all machine actions have been finished
    Connections
    {
        target: machineActionsModel
        onAllFinished:
        {
            if (visible)
            {
                base.showNextPage()
            }
        }
    }

    Label
    {
        id: titleLabel
        anchors.top: parent.top
        anchors.horizontalCenter: parent.horizontalCenter
        horizontalAlignment: Text.AlignHCenter
        text: machineActionsModel.currentItem.title == undefined ? "" : machineActionsModel.currentItem.title
        color: UM.Theme.getColor("primary_button")
        font: UM.Theme.getFont("huge")
        renderType: Text.NativeRendering
    }

    Item
    {
        anchors
        {
            top: titleLabel.bottom
            topMargin: UM.Theme.getSize("default_margin").height
            bottom: nextButton.top
            bottomMargin: UM.Theme.getSize("default_margin").height
            left: parent.left
            right: parent.right
        }

        data: machineActionsModel.currentItem.content == undefined ? emptyItem : machineActionsModel.currentItem.content
    }

    // An empty item in case there's no currentItem.content to show
    Item
    {
        id: emptyItem
    }

    Cura.PrimaryButton
    {
        id: nextButton
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        text: catalog.i18nc("@button", "Next")
        onClicked: machineActionsModel.goToNextAction()
    }
}
