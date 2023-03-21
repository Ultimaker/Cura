// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.15
import QtQuick.Controls 2.9
import QtQuick.Layouts 1.1
import QtQuick.Window 2.1

import UM 1.5 as UM
import Cura 1.5 as Cura

Cura.MachineAction
{
    id: base
    anchors.fill: parent;
    property alias currentItemIndex: listview.currentIndex
    property var selectedDevice: null
    property bool completeProperties: true

    // For validating IP addresses
    property var networkingUtil: Cura.NetworkingUtil {}

    function connectToPrinter()
    {
        if (base.selectedDevice && base.completeProperties)
        {
            manager.associateActiveMachineWithPrinterDevice(base.selectedDevice)
            completed()
        }
    }

    Column
    {
        anchors.fill: parent;
        id: discoverUM3Action
        spacing: UM.Theme.getSize("default_margin").height

        UM.I18nCatalog { id: catalog; name:"cura" }

        UM.Label
        {
            id: pageTitle
            width: parent.width
            text: catalog.i18nc("@title:window", "Connect to Networked Printer")
        }

        UM.Label
        {
            id: pageDescription
            width: parent.width
            text: catalog.i18nc("@label", "To print directly to your printer over the network, please make sure your printer is connected to the network using a network cable or by connecting your printer to your WIFI network. If you don't connect Cura with your printer, you can still use a USB drive to transfer g-code files to your printer.") + "\n\n" + catalog.i18nc("@label", "Select your printer from the list below:")
        }

        Row
        {
            spacing: UM.Theme.getSize("thin_margin").width

            Cura.SecondaryButton
            {
                id: addButton
                text: catalog.i18nc("@action:button", "Add");
                onClicked:
                {
                    manualPrinterDialog.showDialog("", "");
                }
            }

            Cura.SecondaryButton
            {
                id: editButton
                text: catalog.i18nc("@action:button", "Edit")
                enabled: base.selectedDevice != null && base.selectedDevice.getProperty("manual") == "true"
                onClicked:
                {
                    manualPrinterDialog.showDialog(base.selectedDevice.key, base.selectedDevice.ipAddress);
                }
            }

            Cura.SecondaryButton
            {
                id: removeButton
                text: catalog.i18nc("@action:button", "Remove")
                enabled: base.selectedDevice != null && base.selectedDevice.getProperty("manual") == "true"
                onClicked: manager.removeManualDevice(base.selectedDevice.key, base.selectedDevice.ipAddress)
            }

            Cura.SecondaryButton
            {
                id: rediscoverButton
                text: catalog.i18nc("@action:button", "Refresh")
                onClicked: manager.restartDiscovery()
            }
        }

        Row
        {
            id: contentRow
            width: parent.width
            spacing: UM.Theme.getSize("default_margin").width

            Column
            {
                width: Math.round(parent.width * 0.5)
                spacing: UM.Theme.getSize("default_margin").height

                ListView
                {
                    id: listview

                    width: parent.width
                    height: base.height - contentRow.y - discoveryTip.height

                    ScrollBar.vertical: UM.ScrollBar {}
                    clip: true

                    model: manager.foundDevices
                    currentIndex: -1
                    onCurrentIndexChanged:
                    {
                        base.selectedDevice = listview.model[currentIndex];
                        // Only allow connecting if the printer has responded to API query since the last refresh
                        base.completeProperties = base.selectedDevice != null && base.selectedDevice.getProperty("incomplete") != "true";
                    }
                    Component.onCompleted: manager.startDiscovery()

                    delegate: UM.Label
                    {
                        id: printNameLabel
                        width: listview.width
                        height: contentHeight
                        anchors.left: parent.left
                        anchors.leftMargin: UM.Theme.getSize("default_margin").width

                        anchors.right: parent.right
                        text: listview.model[index].name
                        elide: Text.ElideRight

                        MouseArea
                        {
                            anchors.fill: parent;
                            onClicked:
                            {
                                if(!parent.ListView.isCurrentItem)
                                {
                                    parent.ListView.view.currentIndex = index;
                                }
                            }
                        }

                        background: Rectangle
                        {
                            color: parent.ListView.isCurrentItem ? UM.Theme.getColor("background_3") : "transparent"
                        }
                    }
                }
                UM.Label
                {
                    id: discoveryTip
                    anchors.left: parent.left
                    anchors.right: parent.right
                    text: catalog.i18nc("@label", "If your printer is not listed, read the <a href='%1'>network printing troubleshooting guide</a>").arg("https://ultimaker.com/en/cura/troubleshooting/network?utm_source=cura&utm_medium=software&utm_campaign=manage-network-printer");
                    onLinkActivated: Qt.openUrlExternally(link)
                }

            }
            Column
            {
                width: Math.round(parent.width * 0.5)
                visible: base.selectedDevice ? true : false
                spacing: UM.Theme.getSize("default_margin").height
                UM.Label
                {
                    width: parent.width
                    text: base.selectedDevice ? base.selectedDevice.name : ""
                    font: UM.Theme.getFont("large_bold")
                    elide: Text.ElideRight
                }
                GridLayout
                {
                    visible: base.completeProperties
                    width: parent.width
                    columns: 2
                    UM.Label
                    {
                        Layout.fillWidth: true
                        text: catalog.i18nc("@label", "Type")
                    }
                    UM.Label
                    {
                        Layout.fillWidth: true
                        text:
                        {
                            if (base.selectedDevice) {
                                return base.selectedDevice.printerTypeName
                            }
                            return ""
                        }
                    }
                    UM.Label
                    {
                        Layout.fillWidth: true
                        text: catalog.i18nc("@label", "Firmware version")
                    }
                    UM.Label
                    {
                        Layout.fillWidth: true
                        text: base.selectedDevice ? base.selectedDevice.firmwareVersion : ""
                    }
                    UM.Label
                    {
                        Layout.fillWidth: true
                        text: catalog.i18nc("@label", "Address")
                    }
                    UM.Label
                    {
                        Layout.fillWidth: true
                        text: base.selectedDevice ? base.selectedDevice.ipAddress : ""
                    }
                }

                UM.Label
                {
                    width: parent.width
                    text:{
                        // The property cluster size does not exist for older UM3 devices.
                        if(!base.selectedDevice || base.selectedDevice.clusterSize == null || base.selectedDevice.clusterSize == 1)
                        {
                            return "";
                        }
                        else if (base.selectedDevice.clusterSize === 0)
                        {
                            return catalog.i18nc("@label", "This printer is not set up to host a group of printers.");
                        }
                        else
                        {
                            return catalog.i18nc("@label", "This printer is the host for a group of %1 printers.".arg(base.selectedDevice.clusterSize));
                        }
                    }

                }
                UM.Label
                {
                    width: parent.width
                    visible: base.selectedDevice != null && !base.completeProperties
                    text: catalog.i18nc("@label", "The printer at this address has not yet responded." )
                }

                Cura.SecondaryButton
                {
                    text: catalog.i18nc("@action:button", "Connect")
                    enabled: (base.selectedDevice && base.completeProperties && base.selectedDevice.clusterSize > 0) ? true : false
                    onClicked: connectToPrinter()
                }
            }
        }
    }

    Cura.MessageDialog
    {
        id: invalidIPAddressMessageDialog
        title: catalog.i18nc("@title:window", "Invalid IP address")
        text: catalog.i18nc("@text", "Please enter a valid IP address.")
        standardButtons: Dialog.Ok
    }

    Cura.MessageDialog
    {
        id: manualPrinterDialog
        property string printerKey
        property alias addressText: addressField.text

        title: catalog.i18nc("@title:window", "Printer Address")

        width: UM.Theme.getSize("small_popup_dialog").width
        height: UM.Theme.getSize("small_popup_dialog").height

        anchors.centerIn: Overlay.overlay

        standardButtons: Dialog.Yes | Dialog.No

        signal showDialog(string key, string address)
        onShowDialog:
        {
            printerKey = key;
            addressText = address;
            manualPrinterDialog.open();
            addressField.selectAll();
            addressField.focus = true;
        }

        Column {
            anchors.fill: parent
            spacing: UM.Theme.getSize("default_margin").height

            UM.Label
            {
                text: catalog.i18nc("@label", "Enter the IP address of your printer on the network.")
            }

            Cura.TextField
            {
                id: addressField
                width: parent.width
                validator: RegularExpressionValidator { regularExpression: /[a-zA-Z0-9\.\-\_]*/ }
            }
        }

        onAccepted:
        {
            // Validate the input first
            if (!networkingUtil.isValidIP(manualPrinterDialog.addressText))
            {
                // prefent closing of element, as we want to keep the dialog active after a wrongly entered IP adress
                manualPrinterDialog.open()
                // show invalid ip warning
                invalidIPAddressMessageDialog.open();
                return;
            }

            // if the entered IP address has already been discovered, switch the current item to that item
            // and do nothing else.
            for (var i = 0; i < manager.foundDevices.length; i++)
            {
                var device = manager.foundDevices[i]
                if (device.address == manualPrinterDialog.addressText)
                {
                    currentItemIndex = i;
                    return;
                }
            }

            manager.setManualDevice(manualPrinterDialog.printerKey, manualPrinterDialog.addressText);
        }
    }
}
