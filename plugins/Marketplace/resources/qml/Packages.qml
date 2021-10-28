// Copyright (c) 2021 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.15
import QtQuick.Controls 2.15
import UM 1.4 as UM

ScrollView
{
    id: packages
    clip: true
    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

    property alias model: pluginColumn.model

    Component.onCompleted: model.request()

    ListView
    {
        id: pluginColumn
        width: parent.width

        spacing: UM.Theme.getSize("default_margin").height

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
                anchors.leftMargin: Math.round((parent.height - height) / 2)

                text: model.package.displayName
                font: UM.Theme.getFont("medium_bold")
                color: UM.Theme.getColor("text")
            }
        }

        footer: Item //Wrapper item to add spacing between content and footer.
        {
            width: parent.width
            height: UM.Theme.getSize("card").height + pluginColumn.spacing
            Button
            {
                id: loadMoreButton
                width: parent.width
                height: UM.Theme.getSize("card").height
                anchors.bottom: parent.bottom

                enabled: packages.model.hasMore && !packages.model.isLoading || packages.model.errorMessage != ""
                onClicked: packages.model.request()  //Load next page in plug-in list.

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
                            name: "Error"
                            when: packages.model.errorMessage != ""
                            PropertyChanges
                            {
                                target: errorIcon
                                visible: true
                            }
                            PropertyChanges
                            {
                                target: loadMoreIcon
                                visible: false
                            }
                            PropertyChanges
                            {
                                target: loadMoreLabel
                                text: catalog.i18nc("@button", "Failed to load plug-ins:") + " " + packages.model.errorMessage + "\n" + catalog.i18nc("@button", "Retry?")
                            }
                        },
                        State
                        {
                            name: "Loading"
                            when: packages.model.isLoading
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
                            when: !packages.model.hasMore
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

                    Item
                    {
                        width: (errorIcon.visible || loadMoreIcon.visible) ? UM.Theme.getSize("small_button_icon").width : 0
                        height: UM.Theme.getSize("small_button_icon").height
                        anchors.verticalCenter: loadMoreLabel.verticalCenter

                        UM.StatusIcon
                        {
                            id: errorIcon
                            anchors.fill: parent

                            status: UM.StatusIcon.Status.ERROR
                            visible: false
                        }
                        UM.RecolorImage
                        {
                            id: loadMoreIcon
                            anchors.fill: parent

                            source: UM.Theme.getIcon("ArrowDown")
                            color: UM.Theme.getColor("secondary_button_text")

                            RotationAnimator
                            {
                                target: loadMoreIcon
                                from: 0
                                to: 360
                                duration: 1000
                                loops: Animation.Infinite
                                running: packages.model.isLoading
                                alwaysRunToEnd: true
                            }
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
}
