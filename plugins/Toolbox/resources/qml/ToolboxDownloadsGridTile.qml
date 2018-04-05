// Copyright (c) 2018 Ultimaker B.V.
// PluginBrowser is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Dialogs 1.1
import QtQuick.Window 2.2
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import QtQuick.Layouts 1.3
import UM 1.1 as UM

Item
{
    id: base
    height: childrenRect.height
    Layout.alignment: Qt.AlignTop | Qt.AlignLeft
    Row
    {
        width: parent.width
        height: childrenRect.height
        spacing: Math.floor(UM.Theme.getSize("base_unit").width / 2)
        Rectangle
        {
            id: thumbnail
            width: UM.Theme.getSize("toolbox_thumbnail_small").width
            height: UM.Theme.getSize("toolbox_thumbnail_small").height
            color: "white"
            border.width: 1
            Image {
                anchors.centerIn: parent
                width: UM.Theme.getSize("toolbox_thumbnail_small").width - 26
                height: UM.Theme.getSize("toolbox_thumbnail_small").height - 26
                fillMode: Image.PreserveAspectFit
                source: model.icon_url || "../images/logobot.svg"
            }
        }
        Column
        {
            width: parent.width - thumbnail.width - parent.spacing
            spacing: Math.floor(UM.Theme.getSize("base_unit").width / 2)
            Label
            {
                id: name
                text: model.name
                width: parent.width
                wrapMode: Text.WordWrap
                color: UM.Theme.getColor("text")
                font: UM.Theme.getFont("default_bold")
            }
            Label
            {
                id: info
                text:
                {
                    if (model.description.length > 50)
                    {
                        return model.description.substring(0, 50) + "..."
                    }
                    return model.description
                }
                width: parent.width
                wrapMode: Text.WordWrap
                color: UM.Theme.getColor("text_medium")
                font: UM.Theme.getFont("very_small")
            }
        }
    }
    MouseArea
    {
        anchors.fill: parent
        onClicked: {
            console.log(model.id)
            manager.detailView = true
            manager.setDetailData(model.id)
        }
    }
}
