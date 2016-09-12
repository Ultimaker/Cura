import UM 1.2 as UM
import Cura 1.0 as Cura

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1
import QtQuick.Window 2.1

Cura.MachineAction
{
    id: base
    anchors.fill: parent;
    property var selectedPrinter: null
    property var connectingToPrinter: null

    Connections
    {
        target: dialog ? dialog : null
        ignoreUnknownSignals: true
        onNextClicked:
        {
            // Connect to the printer if the MachineAction is currently shown
            if(base.parent == dialog)
            {
                connectToPrinter();
            }
        }
    }

    function connectToPrinter()
    {
        if(base.selectedPrinter)
        {
            var printerKey = base.selectedPrinter.getKey()
            if(connectingToPrinter != printerKey) {
                // prevent an infinite loop
                connectingToPrinter = printerKey;
                manager.setKey(printerKey);
                completed();
            }
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
            text: catalog.i18nc("@title", "Connect to Networked Printer")
            wrapMode: Text.WordWrap
            font.pointSize: 18
        }

        Label
        {
            id: pageDescription
            width: parent.width
            wrapMode: Text.WordWrap
            text: catalog.i18nc("@label", "To print directly to your Ultimaker 3 printer over the network, please make sure your printer is connected to the network using a network cable or by connecting your printer to your WIFI network. If you don't connect Cura with your Ultimaker 3, you can still use a USB drive to transfer g-code files to your printer.\n\nSelect your Ultimaker 3 from the list below:")
        }

        Button
        {
            id: rediscoverButton
            text: catalog.i18nc("@title", "Refresh")
            onClicked: manager.restartDiscovery()
            anchors.right: parent.right
            anchors.rightMargin: parent.width * 0.5
        }

        Row
        {
            id: contentRow
            width: parent.width
            spacing: UM.Theme.getSize("default_margin").width

            Column
            {
                width: parent.width * 0.5
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
                        onModelChanged:
                        {
                            var selectedKey = manager.getStoredKey();
                            for(var i = 0; i < model.length; i++) {
                                if(model[i].getKey() == selectedKey)
                                {
                                    currentIndex = i;
                                    return
                                }
                            }
                            currentIndex = -1;
                        }
                        width: parent.width
                        currentIndex: -1
                        onCurrentIndexChanged: base.selectedPrinter = listview.model[currentIndex]
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
                    //: Tips label
                    //TODO: get actual link from webteam
                    text: catalog.i18nc("@label", "If your Ultimaker 3 is not listed, read the <a href='%1'>Ultimaker 3 network troubleshooting guide</a>").arg("https://ultimaker.com/en/troubleshooting");
                    onLinkActivated: Qt.openUrlExternally(link)
                }

            }
            Column
            {
                width: parent.width * 0.5
                visible: base.selectedPrinter
                spacing: UM.Theme.getSize("default_margin").height
                Label
                {
                    width: parent.width
                    wrapMode: Text.WordWrap
                    text: base.selectedPrinter ? base.selectedPrinter.name : ""
                    font: UM.Theme.getFont("large")
                    elide: Text.ElideRight
                }
                Grid
                {
                    width: parent.width
                    columns: 2
                    Label
                    {
                        width: parent.width * 0.5
                        wrapMode: Text.WordWrap
                        text: catalog.i18nc("@label", "Type")
                    }
                    Label
                    {
                        width: parent.width * 0.5
                        wrapMode: Text.WordWrap
                        text: catalog.i18nc("@label", "Ultimaker 3")
                    }
                    Label
                    {
                        width: parent.width * 0.5
                        wrapMode: Text.WordWrap
                        text: catalog.i18nc("@label", "Firmware version")
                    }
                    Label
                    {
                        width: parent.width * 0.5
                        wrapMode: Text.WordWrap
                        text: base.selectedPrinter ? base.selectedPrinter.firmwareVersion : ""
                    }
                    Label
                    {
                        width: parent.width * 0.5
                        wrapMode: Text.WordWrap
                        text: catalog.i18nc("@label", "IP Address")
                    }
                    Label
                    {
                        width: parent.width * 0.5
                        wrapMode: Text.WordWrap
                        text: base.selectedPrinter ? base.selectedPrinter.ipAddress : ""
                    }
                }

                Button
                {
                    text: catalog.i18nc("@action:button", "Connect")
                    enabled: base.selectedPrinter
                    onClicked: connectToPrinter()
                }
            }
        }
    }
}