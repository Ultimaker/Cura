// Copyright (C) 2021 Ultimaker B.V.
import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.2 as UM
import Cura 1.6 as Cura

Cura.RoundedRectangle
{
    id: base
    cornerSide: Cura.RoundedRectangle.Direction.All
    border.color: UM.Theme.getColor("lining")
    border.width: UM.Theme.getSize("default_lining").width
    radius: UM.Theme.getSize("default_radius").width
    signal clicked()
    property var hasMoreProjectsToLoad
    enabled: hasMoreProjectsToLoad
    color: UM.Theme.getColor("main_background")

    MouseArea
    {
        id: cardMouseArea
        anchors.fill: parent
        hoverEnabled: true
    }

    Row
    {
        id: projectInformationRow
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.verticalCenter: parent.verticalCenter

        UM.RecolorImage
        {
            id: projectImage
            anchors.verticalCenter: parent.verticalCenter
            width: UM.Theme.getSize("section").height
            height: width
            color: UM.Theme.getColor("text_link")
            source: "../images/arrow_down.svg"
        }

        Label
        {
            id: displayNameLabel
            anchors.verticalCenter: parent.verticalCenter
            text: "Load more projects"
            color: UM.Theme.getColor("text_link")
            font: UM.Theme.getFont("medium_bold")
        }
    }

    Component.onCompleted:
    {
        cardMouseArea.clicked.connect(base.clicked)
    }

    states:
    [
        State
        {
            name: "canLoadMoreProjectsAndHovered";
            when: base.hasMoreProjectsToLoad && cardMouseArea.containsMouse
            PropertyChanges
            {
                target: projectImage
                color: UM.Theme.getColor("text_link")
                source: "../images/arrow_down.svg"
            }
            PropertyChanges
            {
                target: displayNameLabel
                color: UM.Theme.getColor("text_link")
                text: "Load more projects"
            }
            PropertyChanges
            {
                target: base
                color: UM.Theme.getColor("action_button_hovered")
            }
        },

        State
        {
            name: "canLoadMoreProjectsAndNotHovered";
            when: base.hasMoreProjectsToLoad && !cardMouseArea.containsMouse
            PropertyChanges
            {
                target: projectImage
                color: UM.Theme.getColor("text_link")
                source: "../images/arrow_down.svg"
            }
            PropertyChanges
            {
                target: displayNameLabel
                color: UM.Theme.getColor("text_link")
                text: "Load more projects"
            }
            PropertyChanges
            {
                target: base
                color: UM.Theme.getColor("main_background")
            }
        },

        State
        {
            name: "noMoreProjectsToLoad"
            when: !base.hasMoreProjectsToLoad
            PropertyChanges
            {
                target: projectImage
                color: UM.Theme.getColor("action_button_disabled_text")
                source: "../images/update.svg"
            }
            PropertyChanges
            {
                target: displayNameLabel
                color: UM.Theme.getColor("action_button_disabled_text")
                text: "No more projects to load"
            }
            PropertyChanges
            {
                target: base
                color: UM.Theme.getColor("action_button_disabled")
            }
        }
    ]
}