// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.3 as UM
import Cura 1.1 as Cura

import "../PrinterSelector"


Item
{
    id: base
    height: networkPrinterScrollView.height + controlsRectangle.height

    property alias maxItemCountAtOnce: networkPrinterScrollView.maxItemCountAtOnce
    property var selectedItem: networkPrinterListView.model[networkPrinterListView.currentIndex]

    ScrollView
    {
        id: networkPrinterScrollView
        anchors.fill: parent

        ScrollBar.horizontal.policy: ScrollBar.AsNeeded
        ScrollBar.vertical.policy: ScrollBar.AlwaysOn

        property int maxItemCountAtOnce: 8  // show at max 8 items at once, otherwise you need to scroll.
        height: maxItemCountAtOnce * UM.Theme.getSize("action_button").height

        clip: true

        ListView
        {
            id: networkPrinterListView
            anchors.fill: parent
            model: CuraApplication.getDiscoveredPrinterModel().discovered_printers
            visible: model.length > 0

            delegate: MachineSelectorButton
            {
                text: modelData.device.name

                anchors.left: parent.left
                anchors.right: parent.right
                anchors.rightMargin: 10
                outputDevice: modelData.device

                checked: ListView.view.currentIndex == index
                onClicked:
                {
                    ListView.view.currentIndex = index
                }
            }
        }
    }

    Cura.RoundedRectangle
    {
        id: controlsRectangle
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: networkPrinterScrollView.bottom
        // Make sure that the left, right, and bottom borders do not show up, otherwise you see double
        // borders.
        anchors.bottomMargin: -border.width
        anchors.leftMargin: -border.width
        anchors.rightMargin: -border.width

        height: UM.Theme.getSize("message_action_button").height + UM.Theme.getSize("default_margin").height
        border.width: UM.Theme.getSize("default_lining").width
        border.color: UM.Theme.getColor("lining")
        color: "white"
        cornerSide: Cura.RoundedRectangle.Direction.Down

        Cura.SecondaryButton
        {
            id: refreshButton
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.getSize("default_margin").width
            anchors.verticalCenter: parent.verticalCenter
            text: catalog.i18nc("@label", "Refresh")
            height: UM.Theme.getSize("message_action_button").height
        }

        Cura.SecondaryButton
        {
            id: addPrinterByIpButton
            anchors.left: refreshButton.right
            anchors.leftMargin: UM.Theme.getSize("default_margin").width
            anchors.verticalCenter: parent.verticalCenter
            text: catalog.i18nc("@label", "Add printer by IP")
            height: UM.Theme.getSize("message_action_button").height
        }

        Item
        {
            id: troubleshootingButton

            anchors.right: parent.right
            anchors.rightMargin: UM.Theme.getSize("default_margin").width
            anchors.verticalCenter: parent.verticalCenter
            height: troubleshoortingLinkIcon.height
            width: troubleshoortingLinkIcon.width + troubleshoortingLabel.width + UM.Theme.getSize("default_margin").width

            UM.RecolorImage
            {
                id: troubleshoortingLinkIcon
                anchors.right: troubleshoortingLabel.left
                anchors.rightMargin: UM.Theme.getSize("default_margin").width
                anchors.verticalCenter: parent.verticalCenter
                height: troubleshoortingLabel.height
                width: height
                sourceSize.height: width
                color: UM.Theme.getColor("text_link")
                source: UM.Theme.getIcon("external_link")
            }

            Label
            {
                id: troubleshoortingLabel
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                text: catalog.i18nc("@label", "Troubleshooting")
                font: UM.Theme.getFont("default")
                color: UM.Theme.getColor("text_link")
                linkColor: UM.Theme.getColor("text_link")
                renderType: Text.NativeRendering
            }

            MouseArea
            {
                anchors.fill: parent
                hoverEnabled: true
                onClicked:
                {
                    // open the material URL with web browser
                    var url = "https://ultimaker.com/incoming-links/cura/material-compatibilty" // TODO
                    Qt.openUrlExternally(url)
                }
                onEntered:
                {
                    troubleshoortingLabel.font.underline = true
                }
                onExited:
                {
                    troubleshoortingLabel.font.underline = false
                }
            }
        }
    }
}
