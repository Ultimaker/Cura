// Copyright (C) 2021 Ultimaker B.V.
import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.5 as UM
import Cura 1.6 as Cura

Cura.RoundedRectangle
{
    id: base
    width: parent.width
    height: projectImage.height + 2 * UM.Theme.getSize("default_margin").width
    cornerSide: Cura.RoundedRectangle.Direction.All
    border.color: enabled ? UM.Theme.getColor("lining") : UM.Theme.getColor("action_button_disabled_border")
    border.width: UM.Theme.getSize("default_lining").width
    radius: UM.Theme.getSize("default_radius").width
    color: getBackgroundColor()
    signal clicked()
    property alias imageSource: projectImage.source
    property alias projectNameText: displayNameLabel.text
    property alias projectUsernameText: usernameLabel.text
    property alias projectLastUpdatedText: lastUpdatedLabel.text
    property alias cardMouseAreaEnabled: cardMouseArea.enabled

    onVisibleChanged: color = getBackgroundColor()

    MouseArea
    {
        id: cardMouseArea
        anchors.fill: parent
        hoverEnabled: base.enabled
        onEntered: color = getBackgroundColor()
        onExited: color = getBackgroundColor()
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
            width: UM.Theme.getSize("card_icon").width
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

            UM.Label
            {
                id: displayNameLabel
                width: parent.width
                height: Math.round(parent.height / 3)
                elide: Text.ElideRight
                font: UM.Theme.getFont("default_bold")
            }

            UM.Label
            {
                id: usernameLabel
                width: parent.width
                height: Math.round(parent.height / 3)
                elide: Text.ElideRight
                color: base.enabled ? UM.Theme.getColor("small_button_text") : UM.Theme.getColor("text_disabled")
            }

            UM.Label
            {
                id: lastUpdatedLabel
                width: parent.width
                height: Math.round(parent.height / 3)
                elide: Text.ElideRight
                color: base.enabled ? UM.Theme.getColor("small_button_text") : UM.Theme.getColor("text_disabled")
            }
        }
    }

    function getBackgroundColor()
    {
        if(enabled)
        {
            if(cardMouseArea.containsMouse)
            {
                return UM.Theme.getColor("action_button_hovered")
            }
            else
            {
                return UM.Theme.getColor("main_background")
            }
        }
        else
        {
            return UM.Theme.getColor("action_button_disabled")
        }
    }
}
