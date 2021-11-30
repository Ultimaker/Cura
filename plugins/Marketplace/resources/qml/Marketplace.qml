// Copyright (c) 2021 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Window 2.2

import UM 1.2 as UM
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

    // Set and unset the content. No need to keep things in memory if it's not visible.
    onVisibleChanged: content.source = visible ? "Plugins.qml" : ""

    Connections
    {
        target: Cura.API.account
        function onLoginStateChanged()
        {
            close();
        }
    }

    title: "Marketplace" //Seen by Ultimaker as a brand name, so this doesn't get translated.
    modality: Qt.NonModal

    // Background color
    Rectangle
    {
        anchors.fill: parent
        anchors.topMargin: UM.Theme.getSize("default_margin").height
        color: UM.Theme.getColor("main_background")

        ColumnLayout
        {
            anchors.fill: parent

            spacing: UM.Theme.getSize("thin_margin").height

            OnboardBanner
            {
                visible: content.item && content.item.bannerVisible
                text: content.item && content.item.bannerText
                icon: content.item && content.item.bannerIcon
                onRemove: content.item && content.item.onRemoveBanner
                readMoreUrl: content.item && content.item.bannerReadMoreUrl
            }

            // Page title.
            Item
            {
                Layout.preferredWidth: parent.width
                Layout.preferredHeight: childrenRect.height

                Label
                {
                    id: pageTitle
                    anchors
                    {
                        left: parent.left
                        leftMargin: UM.Theme.getSize("default_margin").width
                        right: parent.right
                        rightMargin: UM.Theme.getSize("default_margin").width
                    }

                    font: UM.Theme.getFont("large")
                    color: UM.Theme.getColor("text")
                    text: content.item ? content.item.pageTitle: catalog.i18nc("@title", "Loading...")
                }
            }

            // Search & Top-Level Tabs
            Item
            {
                Layout.preferredHeight: childrenRect.height
                Layout.preferredWidth: parent.width - 2 * UM.Theme.getSize("thin_margin").width
                RowLayout
                {
                    width: parent.width
                    height: UM.Theme.getSize("button_icon").height + UM.Theme.getSize("thin_margin").height
                    spacing: UM.Theme.getSize("thin_margin").width

                    Rectangle
                    {
                        color: "transparent"
                        Layout.preferredHeight: parent.height
                        Layout.preferredWidth: searchBar.visible ? UM.Theme.getSize("thin_margin").width : 0
                        Layout.fillWidth: ! searchBar.visible
                    }

                    Cura.SearchBar
                    {
                        id: searchBar
                        Layout.preferredHeight: UM.Theme.getSize("button_icon").height
                        Layout.fillWidth: true
                        onTextEdited: searchStringChanged(text)
                    }

                    // Page selection.
                    TabBar
                    {
                        id: pageSelectionTabBar
                        anchors.right: parent.right
                        height: UM.Theme.getSize("button_icon").height
                        spacing: 0
                        background: Rectangle { color: "transparent" }

                        PackageTypeTab
                        {
                            id: pluginTabText
                            width: implicitWidth
                            text: catalog.i18nc("@button", "Plugins")
                            onClicked:
                            {
                                searchBar.text = ""
                                searchBar.visible = true
                                content.source = "Plugins.qml"
                            }
                        }
                        PackageTypeTab
                        {
                            id: materialsTabText
                            width: implicitWidth
                            text: catalog.i18nc("@button", "Materials")
                            onClicked:
                            {
                                searchBar.text = ""
                                searchBar.visible = true
                                content.source = "Materials.qml"
                            }
                        }
                        ManagePackagesButton
                        {
                            onClicked: content.source = "ManagedPackages.qml"
                        }
                    }

                    TextMetrics
                    {
                        id: pluginTabTextMetrics
                        text: pluginTabText.text
                        font: pluginTabText.font
                    }
                    TextMetrics
                    {
                        id: materialsTabTextMetrics
                        text: materialsTabText.text
                        font: materialsTabText.font
                    }                   
                }
            }

            Cura.TertiaryButton
            {
                text: catalog.i18nc("@info", "Search in the browser")
                iconSource: UM.Theme.getIcon("LinkExternal")

                isIconOnRightSide: true
                font: UM.Theme.getFont("default")

                onClicked: content.item && Qt.openUrlExternally(content.item.searchInBrowserUrl)
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
                    source: "Plugins.qml"

                    Connections
                    {
                        target: content
                        function onLoaded()
                        {
                            pageTitle.text = content.item.pageTitle
                            searchStringChanged.connect(handleSearchStringChanged)
                        }
                        function handleSearchStringChanged(new_search)
                        {
                            content.item.model.searchString = new_search
                        }
                    }
                }
            }
        }
    }
}
