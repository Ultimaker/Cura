// Copyright (c) 2021 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Window 2.2

import UM 1.5 as UM
import Cura 1.6 as Cura

Window
{
    id: marketplaceDialog

    property variant catalog: UM.I18nCatalog { name: "cura" }

    signal searchStringChanged(string new_search)

    minimumWidth: UM.Theme.getSize("modal_window_minimum").width
    minimumHeight: UM.Theme.getSize("modal_window_minimum").height
    width: minimumWidth
    height: minimumHeight

    onVisibleChanged:
    {
        while(contextStack.depth > 1)
        {
            contextStack.pop(); //Do NOT use the StackView.Immediate transition here, since it causes the window to stay empty. Seemingly a Qt bug: https://bugreports.qt.io/browse/QTBUG-60670?
        }
    }

    Connections
    {
        target: Cura.API.account
        function onLoginStateChanged()
        {
            close();
        }
    }

    title: catalog.i18nc("@title", "Install missing Materials")
    modality: Qt.ApplicationModal

    // Background color
    Rectangle
    {
        anchors.fill: parent
        color: UM.Theme.getColor("main_background")
    }
    //The Marketplace can have a page in front of everything with package details. The stack view controls its visibility.
    StackView
    {
        id: contextStack
        anchors.fill: parent

        initialItem: packageBrowse

        ColumnLayout
        {
            id: packageBrowse

            spacing: UM.Theme.getSize("narrow_margin").height

            // Page title.
            Item
            {
                Layout.preferredWidth: parent.width
                Layout.preferredHeight: childrenRect.height + UM.Theme.getSize("default_margin").height

                UM.Label
                {
                    id: pageTitle
                    anchors
                    {
                        left: parent.left
                        leftMargin: UM.Theme.getSize("default_margin").width
                        right: parent.right
                        rightMargin: UM.Theme.getSize("default_margin").width
                        bottom: parent.bottom
                    }

                    font: UM.Theme.getFont("large")
                    text: content.item ? content.item.pageTitle: catalog.i18nc("@title", "Loading...")
                }
            }

            // Page contents.
            Rectangle
            {
                Layout.preferredWidth: parent.width
                Layout.fillHeight: true
                color: UM.Theme.getColor("detail_background")

                // Page contents.
                Loader
                {
                    id: content
                    anchors.fill: parent
                    anchors.margins: UM.Theme.getSize("default_margin").width
                    source: "MissingPackages.qml"
                }
            }
        }
    }

    Rectangle
    {
        height: quitButton.height + 2 * UM.Theme.getSize("default_margin").width
        color: UM.Theme.getColor("primary")
        visible: manager.showRestartNotification
        anchors
        {
            left: parent.left
            right: parent.right
            bottom: parent.bottom
        }

        RowLayout
        {
            anchors
            {
                left: parent.left
                right: parent.right
                verticalCenter: parent.verticalCenter
                margins: UM.Theme.getSize("default_margin").width
            }
            spacing: UM.Theme.getSize("default_margin").width
            UM.ColorImage
            {
                id: bannerIcon
                source: UM.Theme.getIcon("Plugin")

                color: UM.Theme.getColor("primary_button_text")
                implicitWidth: UM.Theme.getSize("banner_icon_size").width
                implicitHeight: UM.Theme.getSize("banner_icon_size").height
            }
            Text
            {
                color: UM.Theme.getColor("primary_button_text")
                text: catalog.i18nc("@button", "In order to use the package you will need to restart Cura")
                font: UM.Theme.getFont("default")
                renderType: Text.NativeRendering
                Layout.fillWidth: true
            }
            Cura.SecondaryButton
            {
                id: quitButton
                text: catalog.i18nc("@info:button, %1 is the application name", "Quit %1").arg(CuraApplication.applicationDisplayName)
                onClicked:
                {
                    marketplaceDialog.hide();
                    CuraApplication.closeApplication();
                }
            }
        }
    }
}
