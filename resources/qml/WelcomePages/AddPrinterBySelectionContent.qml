// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.3 as UM
import Cura 1.1 as Cura

import "../PrinterSelector"


//
// This component contains the content for the "Add a printer" (network) page of the welcome on-boarding process.
//
Item
{
    UM.I18nCatalog { id: catalog; name: "cura" }

    Label
    {
        id: titleLabel
        anchors.top: parent.top
        anchors.topMargin: 40
        anchors.horizontalCenter: parent.horizontalCenter
        horizontalAlignment: Text.AlignHCenter
        text: catalog.i18nc("@label", "Add a printer")
        color: UM.Theme.getColor("primary_button")
        font: UM.Theme.getFont("large_bold")
        renderType: Text.NativeRendering
    }

    DropDownWidget
    {
        id: addNetworkPrinterDropDown

        anchors.top: titleLabel.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: 20

        title: catalog.i18nc("@label", "Add a network printer")

        onClicked:
        {
            if (contentShown)
            {
                addLocalPrinterDropDown.contentShown = false
            }
        }

        contentComponent: networkPrinterListComponent

        Component
        {
            id: networkPrinterListComponent

            Item
            {
                height: networkPrinterScrollView.height + controlsRectangle.height

                ScrollView
                {
                    id: networkPrinterScrollView
                    ScrollBar.horizontal.policy: ScrollBar.AsNeeded
                    ScrollBar.vertical.policy: ScrollBar.AlwaysOn

                    property int maxItemCountAtOnce: 8  // show at max 8 items at once, otherwise you need to scroll.
                    height: maxItemCountAtOnce * (UM.Theme.getSize("action_button").height)

                    clip: true

                    ListView
                    {
                        id: networkPrinterListView
                        anchors.fill: parent
                        model: CuraApplication.getDiscoveredPrinterModel().discovered_printers
                        visible: model.count > 0

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

                    Label
                    {
                        id: noNetworkPrinterLabel
                        text: catalog.i18nc("@label", "There is no printer found over your network.")
                        renderType: Text.NativeRendering
                        visible: !networkPrinterListView.visible
                    }
                }

                Cura.RoundedRectangle
                {
                    id: controlsRectangle
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: networkPrinterScrollView.bottom
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
        }
    }

    DropDownWidget
    {
        id: addLocalPrinterDropDown

        anchors.top: addNetworkPrinterDropDown.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: 20

        title: catalog.i18nc("@label", "Add a non-network printer")

        onClicked:
        {
            if (contentShown)
            {
                addNetworkPrinterDropDown.contentShown = false
            }
        }

        contentComponent: localPrinterListComponent

        Component
        {
            id: localPrinterListComponent

            AddPrinterScrollView
            {
                id: localPrinterView

                ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                ScrollBar.vertical.policy: ScrollBar.AlwaysOn

                property int maxItemCountAtOnce: 10  // show at max 10 items at once, otherwise you need to scroll.
                height: maxItemCountAtOnce * (UM.Theme.getSize("action_button").height)

                clip: true
            }
        }
    }

    Cura.PrimaryButton
    {
        id: nextButton
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.margins: 40
        enabled: true  // TODO
        text: catalog.i18nc("@button", "Next")
        width: 140
        fixedWidthMode: true
        onClicked: base.showNextPage()
    }
}
