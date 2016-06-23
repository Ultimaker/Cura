import UM 1.2 as UM
import Cura 1.0 as Cura

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1
import QtQuick.Window 2.1

Cura.MachineAction
{
    anchors.fill: parent;
    Column
    {
        anchors.fill: parent;
        id: discoverUM3Action
        SystemPalette { id: palette }
        UM.I18nCatalog { id: catalog; name:"cura"}
        Label
        {
            id: pageTitle
            width: parent.width
            text: catalog.i18nc("@title", "Connect to Networked Printer")
            wrapMode: Text.WordWrap
            font.pointSize: 18;
        }

        Label
        {
            id: pageDescription
            width: parent.width
            wrapMode: Text.WordWrap
            text: catalog.i18nc("@label", "To print directly to your Ultimaker 3 printer over the network, please make sure your ptiner is connected to the network using a network cable of by connecting your printer to your WIFI network. \n\n If you don't want to connect Cura with your Ultimaker 3 now, you can always use a USB drive to transfer g-code files to your Printer.\n\n Select your Ultimaker 3 from the list below:")
        }
        Button
        {
            text: "Start looking!"
            onClicked: manager.startDiscovery()
        }
        Row
        {
            width: parent.width
            ScrollView
            {
                id: objectListContainer
                frameVisible: true;
                width: parent.width * 0.5

                Rectangle
                {
                    parent: viewport
                    anchors.fill: parent
                    color: palette.light
                }

                ListView
                {
                    model: manager.foundDevices
                    width: parent.width
                    height: 500
                    currentIndex: activeIndex
                    delegate: Rectangle
                    {
                        height: childrenRect.height;
                        color: ListView.isCurrentItem ? palette.highlight : index % 2 ? palette.base : palette.alternateBase
                        width: parent.width
                        Label
                        {
                            anchors.left: parent.left;
                            anchors.leftMargin: UM.Theme.getSize("default_margin").width;
                            anchors.right: parent.right;
                            text: modelData
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
                                    //base.itemActivated();
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}