// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.3 as UM
import Cura 1.1 as Cura

import "../PrinterSelector"


//
// This is the widget for adding a network printer. There are 2 parts in this widget. One is a scroll view of a list
// of discovered network printers. Beneath the scroll view is a container with 3 buttons: "Refresh", "Add by IP", and
// "Troubleshooting".
//
Item
{
    id: base
    height: networkPrinterInfo.height + controlsRectangle.height

    property alias maxItemCountAtOnce: networkPrinterScrollView.maxItemCountAtOnce
    property var currentItem: (networkPrinterListView.currentIndex >= 0)
                              ? networkPrinterListView.model[networkPrinterListView.currentIndex]
                              : null

    signal refreshButtonClicked()
    signal addByIpButtonClicked()

    Item
    {
        id: networkPrinterInfo
        height: networkPrinterScrollView.visible ? networkPrinterScrollView.height : noPrinterLabel.height
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top

        Label
        {
            id: noPrinterLabel
            height: UM.Theme.getSize("setting_control").height + UM.Theme.getSize("default_margin").height
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.getSize("default_margin").width
            text: catalog.i18nc("@label", "There is no printer found over your network.")
            renderType: Text.NativeRendering
            verticalAlignment: Text.AlignVCenter
            visible: networkPrinterListView.count == 0  // Do not show if there are discovered devices.
        }

        ScrollView
        {
            id: networkPrinterScrollView
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right

            ScrollBar.horizontal.policy: ScrollBar.AsNeeded
            ScrollBar.vertical.policy: ScrollBar.AsNeeded

            property int maxItemCountAtOnce: 8  // show at max 8 items at once, otherwise you need to scroll.
            height: maxItemCountAtOnce * UM.Theme.getSize("action_button").height

            visible: networkPrinterListView.count > 0

            clip: true

            ListView
            {
                id: networkPrinterListView
                anchors.fill: parent
                model: CuraApplication.getDiscoveredPrintersModel().discovered_printers

                Component.onCompleted:
                {
                    // select the first one that's not "unknown" by default.
                    for (var i = 0; i < count; i++)
                    {

                        if (!model[i].is_unknown_machine_type)
                        {
                            currentIndex = i
                            break
                        }
                    }
                }

                delegate: MachineSelectorButton
                {
                    text: modelData.device.name

                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.rightMargin: 10
                    outputDevice: modelData.device

                    enabled: !modelData.is_unknown_machine_type

                    printerTypeLabelAutoFit: true

                    updatePrinterTypesFunction: updateMachineTypes
                    // show printer type as it is
                    printerTypeLabelConversionFunction: function(value) { return value }

                    function updateMachineTypes()
                    {
                        printerTypesList = [ modelData.readable_machine_type ]
                    }

                    checkable: false
                    selected: ListView.view.currentIndex == model.index
                    onClicked:
                    {
                        ListView.view.currentIndex = index
                    }
                }
            }
        }
    }

    Cura.RoundedRectangle
    {
        id: controlsRectangle
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: networkPrinterInfo.bottom
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
            onClicked: base.refreshButtonClicked()
        }

        Cura.SecondaryButton
        {
            id: addPrinterByIpButton
            anchors.left: refreshButton.right
            anchors.leftMargin: UM.Theme.getSize("default_margin").width
            anchors.verticalCenter: parent.verticalCenter
            text: catalog.i18nc("@label", "Add printer by IP")
            height: UM.Theme.getSize("message_action_button").height
            onClicked: base.addByIpButtonClicked()
        }

        Item
        {
            id: troubleshootingButton

            anchors.right: parent.right
            anchors.rightMargin: UM.Theme.getSize("default_margin").width
            anchors.verticalCenter: parent.verticalCenter
            height: troubleshootingLinkIcon.height
            width: troubleshootingLinkIcon.width + troubleshootingLabel.width + UM.Theme.getSize("default_margin").width

            UM.RecolorImage
            {
                id: troubleshootingLinkIcon
                anchors.right: troubleshootingLabel.left
                anchors.rightMargin: UM.Theme.getSize("default_margin").width
                anchors.verticalCenter: parent.verticalCenter
                height: troubleshootingLabel.height
                width: height
                sourceSize.height: width
                color: UM.Theme.getColor("text_link")
                source: UM.Theme.getIcon("external_link")
            }

            Label
            {
                id: troubleshootingLabel
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
                    // open the troubleshooting URL with web browser
                    var url = "https://ultimaker.com/incoming-links/cura/material-compatibilty" // TODO
                    Qt.openUrlExternally(url)
                }
                onEntered:
                {
                    troubleshootingLabel.font.underline = true
                }
                onExited:
                {
                    troubleshootingLabel.font.underline = false
                }
            }
        }
    }
}
