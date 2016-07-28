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
    Column
    {
        anchors.fill: parent;
        id: discoverOctoPrintAction
        SystemPalette { id: palette }
        UM.I18nCatalog { id: catalog; name:"cura" }
        Label
        {
            id: pageTitle
            width: parent.width
            text: catalog.i18nc("@title", "Connect to OctoPrint")
            wrapMode: Text.WordWrap
            font.pointSize: 18
        }

        Label
        {
            id: pageDescription
            width: parent.width
            wrapMode: Text.WordWrap
            text: catalog.i18nc("@label", "Select your OctoPrint instance from the list below:")
        }

        Button
        {
            id: rediscoverButton
            text: catalog.i18nc("@title", "Refresh")
            onClicked: manager.startDiscovery()
            anchors.right: parent.right
            anchors.rightMargin: parent.width * 0.5
        }

        Row
        {
            width: parent.width
            spacing: UM.Theme.getSize("default_margin").width
            ScrollView
            {
                id: objectListContainer
                frameVisible: true
                width: parent.width * 0.5
                height: base.height - parent.y

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
                    currentIndex: activeIndex
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
                    font.pointSize: 16
                    elide: Text.ElideRight
                }
                Grid
                {
                    width: parent.width
                    columns: 2
                    Label
                    {
                        width: parent.width * 0.3
                        wrapMode: Text.WordWrap
                        text: catalog.i18nc("@label", "OctoPrint version")
                    }
                    Label
                    {
                        width: parent.width * 0.7
                        wrapMode: Text.WordWrap
                        text: base.selectedPrinter ? base.selectedPrinter.octoprintVersion : ""
                    }
                    Label
                    {
                        width: parent.width * 0.3
                        wrapMode: Text.WordWrap
                        text: catalog.i18nc("@label", "IP Address")
                    }
                    Label
                    {
                        width: parent.width * 0.7
                        wrapMode: Text.WordWrap
                        text: base.selectedPrinter ? base.selectedPrinter.ipAddress : ""
                    }
                    Label
                    {
                        width: parent.width * 0.3
                        wrapMode: Text.WordWrap
                        text: catalog.i18nc("@label", "API Key")
                    }
                    TextField
                    {
                        id: apiKey
                        width: parent.width * 0.7 - UM.Theme.getSize("default_margin").width
                        text: manager.apiKey
                    }
                }
                Button
                {
                    text: catalog.i18nc("@action", "Open webpage...")
                    onClicked: manager.openWebPage("http://%1/".arg(base.selectedPrinter.ipAddress))
                }
            }
        }
    }
    Button
    {
        text: catalog.i18nc("@action:button", "Ok")
        anchors.right: cancelButton.left
        anchors.bottom: parent.bottom
        onClicked:
        {
            manager.setKey(base.selectedPrinter.getKey())
            manager.setApiKey(apiKey.text)
            completed()
        }
    }
    Button
    {
        id: cancelButton
        text: catalog.i18nc("@action:button", "Cancel")
        anchors.right: discoverOctoPrintAction.right
        anchors.bottom: parent.bottom
        onClicked:
        {
            completed()
        }
    }
}