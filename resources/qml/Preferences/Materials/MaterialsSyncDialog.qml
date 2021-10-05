//Copyright (c) 2021 Ultimaker B.V.
//Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.1
import QtQuick.Controls 2.1
import QtQuick.Layouts 1.15
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

    property alias pageIndex: swipeView.currentIndex

    SwipeView
    {
        id: swipeView
        anchors.fill: parent
        interactive: false

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
                onClicked: {
                    if(Cura.API.account.isLoggedIn)
                    {
                        swipeView.currentIndex += 2; //Skip sign in page.
                    }
                    else
                    {
                        swipeView.currentIndex += 1;
                    }
                }
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

        Rectangle
        {
            id: signinPage
            color: UM.Theme.getColor("main_background")

            ColumnLayout
            {
                spacing: UM.Theme.getSize("default_margin").height
                anchors.fill: parent
                anchors.margins: UM.Theme.getSize("default_margin").width

                Label
                {
                    text: catalog.i18nc("@title:header", "Sign in")
                    font: UM.Theme.getFont("large_bold")
                    color: UM.Theme.getColor("text")
                    Layout.preferredHeight: height
                }
                Label
                {
                    text: catalog.i18nc("@text", "To automatically sync the material profiles with all your printers connected to Digital Factory you need to be signed in in Cura.")
                    font: UM.Theme.getFont("medium")
                    color: UM.Theme.getColor("text")
                    wrapMode: Text.WordWrap
                    width: parent.width
                    Layout.maximumWidth: width
                    Layout.preferredHeight: height
                }
                Item
                {
                    Layout.preferredWidth: parent.width
                    Layout.fillHeight: true
                    Image
                    {
                        source: UM.Theme.getImage("first_run_ultimaker_cloud")
                        width: parent.width / 2
                        sourceSize.width: width
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.horizontalCenter: parent.horizontalCenter
                    }
                }
                Item
                {
                    width: parent.width
                    height: childrenRect.height
                    Layout.preferredHeight: height
                    Cura.SecondaryButton
                    {
                        anchors.left: parent.left
                        text: catalog.i18nc("@button", "Sync materials with USB")
                        onClicked: swipeView.currentIndex = swipeView.count - 1 //Go to the last page, which is USB.
                    }
                    Cura.PrimaryButton
                    {
                        anchors.right: parent.right
                        text: catalog.i18nc("@button", "Sign in")
                        onClicked: Cura.API.account.login()
                    }
                }
            }
        }

        Rectangle
        {
            id: printerListPage
            color: UM.Theme.getColor("main_background")

            ColumnLayout
            {
                spacing: UM.Theme.getSize("default_margin").height
                anchors.fill: parent
                anchors.margins: UM.Theme.getSize("default_margin").width

                Label
                {
                    text: catalog.i18nc("@title:header", "The following printers will receive the new material profiles")
                    font: UM.Theme.getFont("large_bold")
                    color: UM.Theme.getColor("text")
                    Layout.preferredHeight: height
                }
                //TODO: Add contents.
            }
        }
    }
}