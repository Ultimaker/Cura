import QtQuick 2.2
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4

import UM 1.3 as UM
import Cura 1.0 as Cura

Rectangle
{
    id: base
    width: 250 * screenScaleFactor
    height: 250 * screenScaleFactor
    signal clicked()
    MouseArea
    {
        anchors.fill:parent
        onClicked: base.clicked()
    }
    Rectangle
    {
        // TODO: Actually add UM icon / picture
        width: 100 * screenScaleFactor
        height: 100 * screenScaleFactor
        border.width: UM.Theme.getSize("default_lining").width
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: parent.top
        anchors.topMargin: UM.Theme.getSize("default_margin").height
    }
    Label
    {
        id: nameLabel
        anchors.bottom: ipLabel.top
        anchors.bottomMargin:  UM.Theme.getSize("default_margin").height
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.leftMargin: UM.Theme.getSize("default_margin").width
        anchors.rightMargin: UM.Theme.getSize("default_margin").width
        text: modelData.friendly_name.toString()
        font: UM.Theme.getFont("large")
        elide: Text.ElideMiddle;
        height: UM.Theme.getSize("section").height;
    }
    Label
    {
        id: ipLabel
        text: modelData.ip_address.toString()
        anchors.bottom: parent.bottom
        anchors.bottomMargin:  UM.Theme.getSize("default_margin").height
        font: UM.Theme.getFont("default")
        height:10 * screenScaleFactor
        anchors.horizontalCenter: parent.horizontalCenter
    }
}

