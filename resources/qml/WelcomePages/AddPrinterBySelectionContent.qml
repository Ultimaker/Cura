// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.3 as UM
import Cura 1.1 as Cura


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

        title: catalog.i18nc("@label", "Add a networked printer")
        contentShown: true  // by default expand the network printer list

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

            AddNetworkPrinterScrollView
            {
                id: networkPrinterScrollView

                maxItemCountAtOnce: 6  // show at max 6 items at once, otherwise you need to scroll.

                onRefreshButtonClicked:
                {
                    UM.OutputDeviceManager.startDiscovery()
                }

                onAddByIpButtonClicked:
                {
                    base.gotoPage("add_printer_by_ip")
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

        title: catalog.i18nc("@label", "Add a non-networked printer")

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

            AddLocalPrinterScrollView
            {
                id: localPrinterView

                maxItemCountAtOnce: 10  // show at max 10 items at once, otherwise you need to scroll.
            }
        }
    }

    Cura.PrimaryButton
    {
        id: nextButton
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.margins: 40
        enabled:
        {
            // If the network printer dropdown is expanded, make sure that there is a selected item
            if (addNetworkPrinterDropDown.contentShown)
            {
                return addNetworkPrinterDropDown.contentItem.currentItem != null
            }
            else
            {
                return addLocalPrinterDropDown.contentItem.currentItem != null
            }
        }

        text: catalog.i18nc("@button", "Next")
        width: UM.Theme.getSize("welcome_pages_button").width
        fixedWidthMode: true
        onClicked:
        {
            // Create a network printer or a local printer according to the selection
            if (addNetworkPrinterDropDown.contentShown)
            {
                // Create a network printer
                const networkPrinterItem = addNetworkPrinterDropDown.contentItem.currentItem
                CuraApplication.getDiscoveredPrintersModel().createMachineFromDiscoveredPrinter(networkPrinterItem)

                // If we have created a machine, go to the last page, which is the "cloud" page.
                base.gotoPage("cloud")
            }
            else
            {
                // Create a local printer
                const localPrinterItem = addLocalPrinterDropDown.contentItem.currentItem
                Cura.MachineManager.addMachine(localPrinterItem.id)

                base.gotoPage("machine_actions")
            }
        }
    }
}
