// Copyright (C) 2021 Ultimaker B.V.
import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.2 as UM
import Cura 1.6 as Cura

Cura.RoundedRectangle
{
    id: base
    width: parent.width
    height: projectImage.height + 2 * UM.Theme.getSize("default_margin").width
    cornerSide: Cura.RoundedRectangle.Direction.All
    border.color: UM.Theme.getColor("lining")
    border.width: UM.Theme.getSize("default_lining").width
    radius: UM.Theme.getSize("default_radius").width
    color: UM.Theme.getColor("main_background")
    signal clicked()
    property alias imageSource: projectImage.source
    property alias projectNameText: displayNameLabel.text
    property alias projectUsernameText: usernameLabel.text
    property alias projectLastUpdatedText: lastUpdatedLabel.text
    property alias cardMouseAreaEnabled: cardMouseArea.enabled

    onVisibleChanged: color = UM.Theme.getColor("main_background")

    MouseArea
    {
        id: cardMouseArea
        anchors.fill: parent
        hoverEnabled: true
        onEntered: base.color = UM.Theme.getColor("action_button_hovered")
        onExited: base.color = UM.Theme.getColor("main_background")
        onClicked: base.clicked()
    }
    Row
    {
        id: projectInformationRow
        width: parent.width
        padding: UM.Theme.getSize("default_margin").width
        spacing: UM.Theme.getSize("default_margin").width

        Image
        {
            id: projectImage
            anchors.verticalCenter: parent.verticalCenter
            width: UM.Theme.getSize("toolbox_thumbnail_small").width
            height: Math.round(width * 3/4)
            sourceSize.width: width
            sourceSize.height: height
            fillMode: Image.PreserveAspectFit
            mipmap: true
        }
        Column
        {
            id: projectLabelsColumn
            height: projectImage.height
            width: parent.width - x - UM.Theme.getSize("default_margin").width
            anchors.verticalCenter: parent.verticalCenter

            Label
            {
                id: displayNameLabel
                width: parent.width
                height: Math.round(parent.height / 3)
                elide: Text.ElideRight
                color: UM.Theme.getColor("text")
                font: UM.Theme.getFont("default_bold")
            }

            Label
            {
                id: usernameLabel
                width: parent.width
                height: Math.round(parent.height / 3)
                elide: Text.ElideRight
                color: UM.Theme.getColor("small_button_text")
                font: UM.Theme.getFont("default")
            }

            Label
            {
                id: lastUpdatedLabel
                width: parent.width
                height: Math.round(parent.height / 3)
                elide: Text.ElideRight
                color: UM.Theme.getColor("small_button_text")
                font: UM.Theme.getFont("default")
            }
        }
    }
}