//Copyright (c) 2021 Ultimaker B.V.
//Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.1
import QtQuick.Controls 2.1
import QtQuick.Window 2.1
import Cura 1.1 as Cura
import UM 1.2 as UM

Window
{
    id: materialsSyncDialog
    property variant catalog: UM.I18nCatalog { name: "cura" }

    title: catalog.i18nc("@title:window", "Sync materials with printers")
    minimumWidth: UM.Theme.getSize("modal_window_minimum").width
    minimumHeight: UM.Theme.getSize("modal_window_minimum").height
    width: minimumWidth
    height: minimumHeight
    modality: Qt.ApplicationModal

    SwipeView
    {
        id: swipeView
        anchors.fill: parent

        Rectangle
        {
            id: introPage
            color: UM.Theme.getColor("main_background")
            Column
            {
                spacing: UM.Theme.getSize("default_margin").height
                anchors.fill: parent
                anchors.margins: UM.Theme.getSize("default_margin").width

                Label
                {
                    text: catalog.i18nc("@title:header", "Sync materials with printers")
                    font: UM.Theme.getFont("large_bold")
                    color: UM.Theme.getColor("text")
                }
                Label
                {
                    text: catalog.i18nc("@text", "Following a few simple steps, you will be able to synchronize all your material profiles with your printers.")
                    font: UM.Theme.getFont("medium")
                    color: UM.Theme.getColor("text")
                    wrapMode: Text.WordWrap
                    width: parent.width
                }
                Image
                {
                    source: UM.Theme.getImage("material_ecosystem")
                    width: parent.width
                    sourceSize.width: width
                }
            }

            Cura.PrimaryButton
            {
                id: startButton
                anchors
                {
                    right: parent.right
                    rightMargin: UM.Theme.getSize("default_margin").width
                    bottom: parent.bottom
                    bottomMargin: UM.Theme.getSize("default_margin").height
                }
                text: catalog.i18nc("@button", "Start")
                onClicked: swipeView.currentIndex += 1
            }
            Cura.TertiaryButton
            {
                anchors
                {
                    left: parent.left
                    leftMargin: UM.Theme.getSize("default_margin").width
                    verticalCenter: startButton.verticalCenter
                }
                text: catalog.i18nc("@button", "Why do I need to sync material profiles?")
                iconSource: UM.Theme.getIcon("LinkExternal")
                isIconOnRightSide: true
                onClicked: Qt.openUrlExternally("https://ultimaker.com")
            }
        }
    }
}