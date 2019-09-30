// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import UM 1.2 as UM
import Cura 1.5 as Cura

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1
import QtQuick.Window 2.1
import QtQuick.Dialogs 1.2

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

        SystemPalette { id: palette }
        UM.I18nCatalog { id: catalog; name:"cura" }
        Label
        {
            id: pageTitle
            width: parent.width
            text: catalog.i18nc("@title:window", "Connect to Networked Printer")
            wrapMode: Text.WordWrap
            renderType: Text.NativeRendering
            font.pointSize: 18
        }

        Label
        {
            id: pageDescription
            width: parent.width
            wrapMode: Text.WordWrap
            renderType: Text.NativeRendering
            text: catalog.i18nc("@label", "To print directly to your printer over the network, please make sure your printer is connected to the network using a network cable or by connecting your printer to your WIFI network. If you don't connect Cura with your printer, you can still use a USB drive to transfer g-code files to your printer.") + "\n\n" + catalog.i18nc("@label", "Select your printer from the list below:")
        }

        Row
        {
            spacing: UM.Theme.getSize("default_lining").width

            Button
            {
                id: addButton
                text: catalog.i18nc("@action:button", "Add");
                onClicked:
                {
                    manualPrinterDialog.showDialog("", "");
                }
            }

            Button
            {
                id: editButton
                text: catalog.i18nc("@action:button", "Edit")
                enabled: base.selectedDevice != null && base.selectedDevice.getProperty("manual") == "true"
                onClicked:
                {
                    manualPrinterDialog.showDialog(base.selectedDevice.key, base.selectedDevice.ipAddress);
                }
            }

            Button
            {
                id: removeButton
                text: catalog.i18nc("@action:button", "Remove")
                enabled: base.selectedDevice != null && base.selectedDevice.getProperty("manual") == "true"
                onClicked: manager.removeManualDevice(base.selectedDevice.key, base.selectedDevice.ipAddress)
            }

            Button
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

                ScrollView
                {
                    id: objectListContainer
                    frameVisible: true
                    width: parent.width
                    height: base.height - contentRow.y - discoveryTip.height

                    Rectangle
                    {
                        parent: viewport
                        anchors.fill: parent
                        color: palette.light
                    }

                    ListView
                    {
                        id: listview
                        model: manager.foundDevices
                        width: parent.width
                        currentIndex: -1
                        onCurrentIndexChanged:
                        {
                            base.selectedDevice = listview.model[currentIndex];
                            // Only allow connecting if the printer has responded to API query since the last refresh
                            base.completeProperties = base.selectedDevice != null && base.selectedDevice.getProperty("incomplete") != "true";
                        }
                        Component.onCompleted: manager.startDiscovery()
                        delegate: Rectangle
                        {
                            height: childrenRect.height
                            color: ListView.isCurrentItem ? palette.highlight : index % 2 ? palette.base : palette.alternateBase
                            width: parent.width
                            Label
                            {
                                anchors.left: parent.left
                                anchors.leftMargin: UM.Theme.getSize("default_margin").width
                                anchors.right: parent.right
                                text: listview.model[index].name
                                color: parent.ListView.isCurrentItem ? palette.highlightedText : palette.text
                                elide: Text.ElideRight
                                renderType: Text.NativeRendering
                            }

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
                        }
                    }
                }
                Label
                {
                    id: discoveryTip
                    anchors.left: parent.left
                    anchors.right: parent.right
                    wrapMode: Text.WordWrap
                    renderType: Text.NativeRendering
                    text: catalog.i18nc("@label", "If your printer is not listed, read the <a href='%1'>network printing troubleshooting guide</a>").arg("https://ultimaker.com/en/troubleshooting");
                    onLinkActivated: Qt.openUrlExternally(link)
                }

            }
            Column
            {
                width: Math.round(parent.width * 0.5)
                visible: base.selectedDevice ? true : false
                spacing: UM.Theme.getSize("default_margin").height
                Label
                {
                    width: parent.width
                    wrapMode: Text.WordWrap
                    text: base.selectedDevice ? base.selectedDevice.name : ""
                    font: UM.Theme.getFont("large_bold")
                    elide: Text.ElideRight
                    renderType: Text.NativeRendering
                }
                Grid
                {
                    visible: base.completeProperties
                    width: parent.width
                    columns: 2
                    Label
                    {
                        width: Math.round(parent.width * 0.5)
                        wrapMode: Text.WordWrap
                        renderType: Text.NativeRendering
                        text: catalog.i18nc("@label", "Type")
                    }
                    Label
                    {
                        width: Math.round(parent.width * 0.5)
                        wrapMode: Text.WordWrap
                        renderType: Text.NativeRendering
                        text:
                        {
                            if (base.selectedDevice) {
                                return base.selectedDevice.printerTypeName
                            }
                            return ""
                        }
                    }
                    Label
                    {
                        width: Math.round(parent.width * 0.5)
                        wrapMode: Text.WordWrap
                        renderType: Text.NativeRendering
                        text: catalog.i18nc("@label", "Firmware version")
                    }
                    Label
                    {
                        width: Math.round(parent.width * 0.5)
                        wrapMode: Text.WordWrap
                        renderType: Text.NativeRendering
                        text: base.selectedDevice ? base.selectedDevice.firmwareVersion : ""
                    }
                    Label
                    {
                        width: Math.round(parent.width * 0.5)
                        wrapMode: Text.WordWrap
                        renderType: Text.NativeRendering
                        text: catalog.i18nc("@label", "Address")
                    }
                    Label
                    {
                        width: Math.round(parent.width * 0.5)
                        wrapMode: Text.WordWrap
                        renderType: Text.NativeRendering
                        text: base.selectedDevice ? base.selectedDevice.ipAddress : ""
                    }
                }

                Label
                {
                    width: parent.width
                    wrapMode: Text.WordWrap
                    renderType: Text.NativeRendering
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
                Label
                {
                    width: parent.width
                    wrapMode: Text.WordWrap
                    renderType: Text.NativeRendering
                    visible: base.selectedDevice != null && !base.completeProperties
                    text: catalog.i18nc("@label", "The printer at this address has not yet responded." )
                }

                Button
                {
                    text: catalog.i18nc("@action:button", "Connect")
                    enabled: (base.selectedDevice && base.completeProperties && base.selectedDevice.clusterSize > 0) ? true : false
                    onClicked: connectToPrinter()
                }
            }
        }
    }

    MessageDialog
    {
        id: invalidIPAddressMessageDialog
        x: (parent.x + (parent.width) / 2) | 0
        y: (parent.y + (parent.height) / 2) | 0
        title: catalog.i18nc("@title:window", "Invalid IP address")
        text: catalog.i18nc("@text", "Please enter a valid IP address.")
        icon: StandardIcon.Warning
        standardButtons: StandardButton.Ok
    }

    UM.Dialog
    {
        id: manualPrinterDialog
        property string printerKey
        property alias addressText: addressField.text

        title: catalog.i18nc("@title:window", "Printer Address")

        minimumWidth: 400 * screenScaleFactor
        minimumHeight: 130 * screenScaleFactor
        width: minimumWidth
        height: minimumHeight

        signal showDialog(string key, string address)
        onShowDialog:
        {
            printerKey = key;
            addressText = address;
            manualPrinterDialog.show();
            addressField.selectAll();
            addressField.focus = true;
        }

        Column {
            anchors.fill: parent
            spacing: UM.Theme.getSize("default_margin").height

            Label
            {
                text: catalog.i18nc("@label", "Enter the IP address of your printer on the network.")
                width: parent.width
                wrapMode: Text.WordWrap
                renderType: Text.NativeRendering
            }

            TextField
            {
                id: addressField
                width: parent.width
                validator: RegExpValidator
                {
                    regExp: /[a-zA-Z0-9\.\-\_]*/
                }

                onAccepted: btnOk.clicked()
            }
        }

        rightButtons: [
            Button {
                text: catalog.i18nc("@action:button","Cancel")
                onClicked:
                {
                    manualPrinterDialog.reject()
                    manualPrinterDialog.hide()
                }
            },
            Button {
                id: btnOk
                text: catalog.i18nc("@action:button", "OK")
                onClicked:
                {
                    // Validate the input first
                    if (!networkingUtil.isValidIP(manualPrinterDialog.addressText))
                    {
                        invalidIPAddressMessageDialog.open()
                        return
                    }

                    // if the entered IP address has already been discovered, switch the current item to that item
                    // and do nothing else.
                    for (var i = 0; i < manager.foundDevices.length; i++)
                    {
                        var device = manager.foundDevices[i]
                        if (device.address == manualPrinterDialog.addressText)
                        {
                            currentItemIndex = i
                            manualPrinterDialog.hide()
                            return
                        }
                    }

                    manager.setManualDevice(manualPrinterDialog.printerKey, manualPrinterDialog.addressText)
                    manualPrinterDialog.hide()
                }
                enabled: manualPrinterDialog.addressText.trim() != ""
                isDefault: true
            }
        ]
    }
}
