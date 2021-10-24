// Copyright (c) 2021 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.15
import QtQuick.Controls 2.15
import Cura 1.7 as Cura
import UM 1.0 as UM

ScrollView
{
    clip: true

    Column
    {
        id: pluginColumn
        width: parent.width
        spacing: UM.Theme.getSize("default_margin").height

        Repeater
        {
            model: Cura.PackageList
            {
                id: pluginList
            }

            delegate: Rectangle
            {
                width: pluginColumn.width
                height: UM.Theme.getSize("card").height

                color: UM.Theme.getColor("main_background")
                radius: UM.Theme.getSize("default_radius").width

                Label
                {
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.left: parent.left
                    anchors.leftMargin: (parent.height - height) / 2

                    text: model.package.displayName
                    font: UM.Theme.getFont("medium_bold")
                    color: UM.Theme.getColor("text")
                }
            }
        }
        Button
        {
            id: loadMoreButton
            width: parent.width
            height: UM.Theme.getSize("card").height

            enabled: pluginList.hasMore && !pluginList.isLoading
            onClicked: pluginList.request()  //Load next page in plug-in list.

            background: Rectangle
            {
                anchors.fill: parent
                radius: UM.Theme.getSize("default_radius").width
                color: UM.Theme.getColor("main_background")
            }

            Row
            {
                anchors.centerIn: parent

                spacing: UM.Theme.getSize("thin_margin").width

                states:
                [
                    State
                    {
                        name: "Loading"
                        when: pluginList.isLoading
                        PropertyChanges
                        {
                            target: loadMoreIcon
                            source: UM.Theme.getIcon("ArrowDoubleCircleRight")
                            color: UM.Theme.getColor("action_button_disabled_text")
                        }
                        PropertyChanges
                        {
                            target: loadMoreLabel
                            text: catalog.i18nc("@button", "Loading")
                            color: UM.Theme.getColor("action_button_disabled_text")
                        }
                    },
                    State
                    {
                        name: "LastPage"
                        when: !pluginList.hasMore
                        PropertyChanges
                        {
                            target: loadMoreIcon
                            visible: false
                        }
                        PropertyChanges
                        {
                            target: loadMoreLabel
                            text: catalog.i18nc("@button", "No more results to load")
                            color: UM.Theme.getColor("action_button_disabled_text")
                        }
                    }
                ]

                UM.RecolorImage
                {
                    id: loadMoreIcon
                    width: visible ? UM.Theme.getSize("small_button_icon").width : 0
                    height: UM.Theme.getSize("small_button_icon").height
                    anchors.verticalCenter: loadMoreLabel.verticalCenter

                    source: UM.Theme.getIcon("ArrowDown")
                    color: UM.Theme.getColor("secondary_button_text")

                    RotationAnimator
                    {
                        target: loadMoreIcon
                        from: 0
                        to: 360
                        duration: 1000
                        loops: Animation.Infinite
                        running: pluginList.isLoading
                        alwaysRunToEnd: true
                    }
                }
                Label
                {
                    id: loadMoreLabel
                    text: catalog.i18nc("@button", "Load more")
                    font: UM.Theme.getFont("medium_bold")
                    color: UM.Theme.getColor("secondary_button_text")
                }
            }
        }
    }
}