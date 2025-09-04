// Copyright (c) 2022 Ultimaker B.V.
// Uranium is released under the terms of the LGPLv3 or higher.

import QtQuick 2.1
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.1
import QtQuick.Window 2.1

import ".."

import UM 1.6 as UM

UM.Dialog
{
    id: base

    title: catalog.i18nc("@title:window", "Preferences")
    minimumWidth: UM.Theme.getSize("modal_window_minimum").width
    minimumHeight: UM.Theme.getSize("modal_window_minimum").height
    width: minimumWidth
    height: minimumHeight
    backgroundColor: UM.Theme.getColor("background_2")

    property alias currentPage: pagesList.currentIndex
    property alias currentItem: pagesList.currentItem

    Item
    {
        id: test
        anchors.fill: parent

        ListView
        {
            id: pagesList
            width: UM.Theme.getSize("preferences_page_list_item").width
            anchors.top: parent.top
            anchors.bottom: parent.bottom

            ScrollBar.vertical: UM.ScrollBar {}
            clip: true
            model: [
                {
                    name: catalog.i18nc("@title:tab", "General"),
                    item: Qt.resolvedUrl("GeneralPage.qml")
                },
                {
                    name: catalog.i18nc("@title:tab", "Settings"),
                    item: Qt.resolvedUrl("SettingVisibilityPage.qml")
                },
                {
                    name: catalog.i18nc("@title:tab", "Printers"),
                    item: Qt.resolvedUrl("MachinesPage.qml")
                },
                {
                    name: catalog.i18nc("@title:tab", "Materials"),
                    item: Qt.resolvedUrl("Materials/MaterialsPage.qml")
                },
                {
                    name: catalog.i18nc("@title:tab", "Profiles"),
                    item: Qt.resolvedUrl("ProfilesPage.qml")
                }
            ]

            delegate: Rectangle
            {
                width: parent ? parent.width : 0
                height: pageLabel.height

                color: ListView.isCurrentItem ? UM.Theme.getColor("background_3") : UM.Theme.getColor("main_background")

                UM.Label
                {
                    id: pageLabel
                    anchors.centerIn: parent
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignHCenter
                    width: parent.width
                    height: UM.Theme.getSize("preferences_page_list_item").height
                    color: UM.Theme.getColor("text_default")
                    text: modelData.name
                }
                MouseArea
                {
                    anchors.fill: parent
                    onClicked: pagesList.currentIndex = index
                }
            }

            onCurrentIndexChanged: stackView.replace(model[currentIndex].item)
        }

        StackView
        {
            id: stackView
            anchors
            {
                left: pagesList.right
                leftMargin: UM.Theme.getSize("narrow_margin").width
                top: parent.top
                bottom: parent.bottom
                right: parent.right
            }

            initialItem: Item { property bool resetEnabled: false }

            replaceEnter: Transition
            {
                NumberAnimation
                {
                    properties: "opacity"
                    from: 0
                    to: 1
                    duration: 100
                }
            }
            replaceExit: Transition
            {
                NumberAnimation
                {
                    properties: "opacity"
                    from: 1
                    to: 0
                    duration: 100
                }
            }
        }

        UM.I18nCatalog { id: catalog; name: "uranium"; }
    }
}
