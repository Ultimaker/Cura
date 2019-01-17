// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4

import UM 1.2 as UM
import Cura 1.0 as Cura


Item
{
    id: tipsCell
    anchors.top: adhesionCheckBox.visible ? adhesionCheckBox.bottom : (enableSupportCheckBox.visible ? supportExtruderCombobox.bottom : infillCellRight.bottom)
    anchors.topMargin: Math.round(UM.Theme.getSize("sidebar_margin").height * 2)
    anchors.left: parent.left
    width: parent.width
    height: tipsText.contentHeight * tipsText.lineCount

    Label
    {
        id: tipsText
        anchors.left: parent.left
        anchors.leftMargin: UM.Theme.getSize("sidebar_margin").width
        anchors.right: parent.right
        anchors.rightMargin: UM.Theme.getSize("sidebar_margin").width
        anchors.top: parent.top
        wrapMode: Text.WordWrap
        text: catalog.i18nc("@label", "Need help improving your prints?<br>Read the <a href='%1'>Ultimaker Troubleshooting Guides</a>").arg("https://ultimaker.com/en/troubleshooting")
        font: UM.Theme.getFont("default")
        color: UM.Theme.getColor("text")
        linkColor: UM.Theme.getColor("text_link")
        onLinkActivated: Qt.openUrlExternally(link)
    }
}