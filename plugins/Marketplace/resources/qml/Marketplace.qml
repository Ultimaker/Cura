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

    property alias showOnboadBanner: onBoardBanner.visible
    property alias showSearchHeader: searchHeader.visible
    property alias pageContentsSource: content.source

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

    title: "Marketplace" //Seen by Ultimaker as a brand name, so this doesn't get translated.
    modality: Qt.NonModal

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

            OnboardBanner
            {
                id: onBoardBanner
                visible: content.item && content.item.bannerVisible
                text: content.item && content.item.bannerText
                icon: content.item && content.item.bannerIcon
                onRemove: content.item && content.item.onRemoveBanner
                readMoreUrl: content.item && content.item.bannerReadMoreUrl

                Layout.fillWidth: true
                Layout.leftMargin: UM.Theme.getSize("default_margin").width
                Layout.rightMargin: UM.Theme.getSize("default_margin").width
            }

            // Search & Top-Level Tabs
            Item
            {
                id: searchHeader
                implicitHeight: childrenRect.height
                implicitWidth: parent.width - 2 * UM.Theme.getSize("default_margin").width
                Layout.alignment: Qt.AlignHCenter
                RowLayout
                {
                    width: parent.width
                    height: UM.Theme.getSize("button_icon").height + UM.Theme.getSize("default_margin").height
                    spacing: UM.Theme.getSize("thin_margin").width

                    Cura.SearchBar
                    {
                        id: searchBar
                        implicitHeight: UM.Theme.getSize("button_icon").height
                        Layout.fillWidth: true
                        onTextEdited: searchStringChanged(text)
                    }

                    // Page selection.
                    TabBar
                    {
                        id: pageSelectionTabBar
                        Layout.alignment: Qt.AlignRight
                        height: UM.Theme.getSize("button_icon").height
                        spacing: 0
                        background: Rectangle { color: "transparent" }
                        currentIndex: manager.tabShown

                        onCurrentIndexChanged:
                        {
                            manager.tabShown = currentIndex
                            searchBar.text = "";
                            searchBar.visible = currentItem.hasSearch;
                            content.source = currentItem.sourcePage;
                        }

                        PackageTypeTab
                        {
                            id: pluginTabText
                            width: implicitWidth
                            text: catalog.i18nc("@button", "Plugins")
                            property string sourcePage: "Plugins.qml"
                            property bool hasSearch: true
                        }
                        PackageTypeTab
                        {
                            id: materialsTabText
                            width: implicitWidth
                            text: catalog.i18nc("@button", "Materials")
                            property string sourcePage: "Materials.qml"
                            property bool hasSearch: true
                        }
                        ManagePackagesButton
                        {
                            property string sourcePage: "ManagedPackages.qml"
                            property bool hasSearch: false

                            Cura.NotificationIcon
                            {
                                anchors
                                {
                                    horizontalCenter: parent.right
                                    verticalCenter: parent.top
                                }
                                visible: CuraApplication.getPackageManager().packagesWithUpdate.length > 0

                                labelText:
                                {
                                    const itemCount = CuraApplication.getPackageManager().packagesWithUpdate.length
                                    return itemCount > 9 ? "9+" : itemCount
                                }
                            }
                        }
                    }
                }
            }

            FontMetrics
            {
                id: fontMetrics
                font: UM.Theme.getFont("default")
            }

            Cura.TertiaryButton
            {
                text: catalog.i18nc("@info", "Search in the browser")
                iconSource: UM.Theme.getIcon("LinkExternal")
                visible: pageSelectionTabBar.currentItem.hasSearch && searchHeader.visible
                isIconOnRightSide: true
                height: fontMetrics.height
                textFont: fontMetrics.font
                textColor: UM.Theme.getColor("text")

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
                    CuraApplication.checkAndExitApplication();
                }
            }
        }
    }

    Rectangle
    {
        color: UM.Theme.getColor("main_background")
        anchors.fill: parent
        visible: !Cura.API.account.isLoggedIn && CuraApplication.isEnterprise

        UM.Label
        {
            id: signInLabel
            anchors.centerIn: parent
            width: Math.round(UM.Theme.getSize("modal_window_minimum").width / 2.5)
            text: catalog.i18nc("@description","Please sign in to get verified plugins and materials for UltiMaker Cura Enterprise")
            horizontalAlignment: Text.AlignHCenter
        }

        Cura.PrimaryButton
        {
            id: loginButton
            width: UM.Theme.getSize("account_button").width
            height: UM.Theme.getSize("account_button").height
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: signInLabel.bottom
            anchors.topMargin: UM.Theme.getSize("default_margin").height * 2
            text: catalog.i18nc("@button", "Sign in")
            fixedWidthMode: true
            onClicked: Cura.API.account.login()
        }
    }
}
