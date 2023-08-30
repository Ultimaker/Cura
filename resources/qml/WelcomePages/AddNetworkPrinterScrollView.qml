// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Layouts 2.3

import UM 1.5 as UM
import Cura 1.1 as Cura

//
// This is the widget for adding a network printer. There are 2 parts in this widget. One is a scroll view of a list
// of discovered network printers. Beneath the scroll view is a container with 3 buttons: "Refresh", "Add by IP", and
// "Troubleshooting".
//
Item
{
    id: base

    property var currentItem: (networkPrinterListView.currentIndex >= 0)
                              ? networkPrinterListView.model[networkPrinterListView.currentIndex]
                              : null

    signal refreshButtonClicked()
    signal addByIpButtonClicked()
    signal addCloudPrinterButtonClicked()

    Item
    {
        id: networkPrinterInfo
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: separator.top

        UM.Label
        {
            id: noPrinterLabel
            height: UM.Theme.getSize("setting_control").height + UM.Theme.getSize("default_margin").height
            anchors.fill: parent
            anchors.margins: UM.Theme.getSize("default_margin").width
            text: catalog.i18nc("@label", "There is no printer found over your network.")
            visible: networkPrinterListView.count == 0  // Do not show if there are discovered devices.
            verticalAlignment: Text.AlignTop
        }

        ListView
        {
            id: networkPrinterListView
            anchors.fill: parent

            ScrollBar.vertical: UM.ScrollBar
            {
                id: networkPrinterScrollBar
            }
            clip: true
            visible: networkPrinterListView.count > 0

            model: contentLoader.enabled ? CuraApplication.getDiscoveredPrintersModel().discoveredPrinters: undefined
            cacheBuffer: 1000000   // Set a large cache to effectively just cache every list item.

            section.property: "modelData.sectionName"
            section.criteria: ViewSection.FullString
            section.delegate: UM.Label
            {
                anchors.left: parent.left
                anchors.leftMargin: UM.Theme.getSize("default_margin").width
                width: parent.width - networkPrinterScrollBar.width - UM.Theme.getSize("default_margin").width
                height: UM.Theme.getSize("setting_control").height
                text: section
                color: UM.Theme.getColor("small_button_text")
            }

            Component.onCompleted:
            {
                var toSelectIndex = -1
                // Select the first one that's not "unknown" and is the host a group by default.
                for (var i = 0; i < count; i++)
                {
                    if (!model[i].isUnknownMachineType && model[i].isHostOfGroup)
                    {
                        toSelectIndex = i
                        break
                    }
                }
                currentIndex = toSelectIndex
            }

            // CURA-6483 For some reason currentIndex can be reset to 0. This check is here to prevent automatically
            // selecting an unknown or non-host printer.
            onCurrentIndexChanged:
            {
                var item = model[currentIndex]
                if (!item || item.isUnknownMachineType || !item.isHostOfGroup)
                {
                    currentIndex = -1
                }
            }

            delegate: Cura.MachineSelectorButton
            {
                text: modelData.device.name

                width: networkPrinterListView.width - networkPrinterScrollBar.width
                outputDevice: modelData.device

                enabled: !modelData.isUnknownMachineType && modelData.isHostOfGroup

                printerTypeLabelAutoFit: true

                // update printer types for all items in the list
                updatePrinterTypesOnlyWhenChecked: false
                updatePrinterTypesFunction: updateMachineTypes
                // show printer type as it is
                printerTypeLabelConversionFunction: function(value) { return value }

                function updateMachineTypes()
                {
                    printerTypesList = [ modelData.readableMachineType ]
                }

                checkable: false
                selected: networkPrinterListView.currentIndex == model.index
                onClicked:
                {
                    networkPrinterListView.currentIndex = index
                }
            }
        }
    }

    // Horizontal line separating the buttons (below) and the discovered network printers (above)
    Rectangle
    {
        id: separator
        anchors.left: parent.left
        anchors.bottom: controlsRectangle.top
        anchors.right: parent.right
        height: UM.Theme.getSize("default_lining").height
        color: UM.Theme.getColor("lining")
    }

    Item
    {
        id: controlsRectangle
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom

        height: UM.Theme.getSize("message_action_button").height + UM.Theme.getSize("default_margin").height

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
            anchors.rightMargin: UM.Theme.getSize("thin_margin").width
            anchors.verticalCenter: parent.verticalCenter
            height: troubleshootingLinkIcon.height
            width: troubleshootingLinkIcon.width + troubleshootingLabel.width + UM.Theme.getSize("thin_margin").width

            UM.ColorImage
            {
                id: troubleshootingLinkIcon
                anchors.right: troubleshootingLabel.left
                anchors.rightMargin: UM.Theme.getSize("thin_margin").width
                anchors.verticalCenter: parent.verticalCenter
                height: troubleshootingLabel.height
                width: height
                color: UM.Theme.getColor("text_link")
                source: UM.Theme.getIcon("LinkExternal")
            }

            UM.Label
            {
                id: troubleshootingLabel
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                text: catalog.i18nc("@label", "Troubleshooting")
                color: UM.Theme.getColor("text_link")
            }

            MouseArea
            {
                anchors.fill: parent
                hoverEnabled: true
                onClicked:
                {
                    // open the troubleshooting URL with web browser
                    const url = "https://ultimaker.com/in/cura/troubleshooting/network?utm_source=cura&utm_medium=software&utm_campaign=add-network-printer"
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
