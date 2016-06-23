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
        UM.I18nCatalog { id: catalog; name:"cura"}
        Label
        {
            id: pageTitle
            width: parent.width
            text: catalog.i18nc("@title", "Discover Printer")
            wrapMode: Text.WordWrap
            font.pointSize: 18;
        }
        Button
        {
            text: "Start looking!"
            onClicked: manager.startDiscovery()
        }

        ListView
        {
            model: manager.foundDevices
            width: parent.width
            height: 500
            delegate: Rectangle
            {
                height: childrenRect.height;
                color: "white"
                width: parent.width
                Label
                {
                    anchors.left: parent.left;
                    anchors.leftMargin: UM.Theme.getSize("default_margin").width;
                    anchors.right: parent.right;
                    text: modelData
                    elide: Text.ElideRight
                }
            }
        }
    }
}