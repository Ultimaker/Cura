// Copyright (c) 2025 UltiMaker
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.4
import QtQuick.Controls 2.9
import QtQuick.Layouts 1.3

import UM 1.6 as UM
import Cura 1.6 as Cura

UM.Dialog
{
    readonly property UM.I18nCatalog catalog: UM.I18nCatalog { name: "cura" }

    id: base

    title: catalog.i18nc("@title:window The argument is the application name.", "About %1").arg(CuraApplication.applicationDisplayName)

    // Flag to toggle between main dependencies information and extensive dependencies information
    property bool showDefaultDependencies: true

    minimumHeight: 700 * screenScaleFactor
    height: minimumHeight

    backgroundColor: UM.Theme.getColor("main_background")

    headerComponent: Rectangle
    {
        width: parent.width
        height: logo.height + 2 * UM.Theme.getSize("wide_margin").height
        color: UM.Theme.getColor("main_window_header_background")

        Image
        {
            id: logo
            width: Math.floor(base.width * 0.85)
            height: Math.floor(width * UM.Theme.getSize("logo").height / UM.Theme.getSize("logo").width)
            source: UM.Theme.getImage("logo")
            sourceSize.width: width
            sourceSize.height: height
            fillMode: Image.PreserveAspectFit

            anchors.centerIn: parent
        }

        Image
        {
            id: enterpriseLogo
            visible: CuraApplication.isEnterprise
            source: UM.Theme.getImage("enterprise")
            fillMode: Image.PreserveAspectFit

            anchors.bottom: parent.bottom
        }

        UM.Label
        {
            id: version
            text: catalog.i18nc("@label","version: %1").arg(CuraApplication.version())
            font: UM.Theme.getFont("large_bold")
            color: UM.Theme.getColor("button_text")
            anchors.right : logo.right
            anchors.top: logo.bottom
        }

        MouseArea
        {
            anchors.fill: parent
            onDoubleClicked: showDefaultDependencies = !showDefaultDependencies
        }
    }

    // Reusable component to display a dependency
    readonly property Component dependency_row: RowLayout
    {
        spacing: UM.Theme.getSize("default_margin").width

        UM.Label
        {
            text: {
                if (url !== "") {
                    return `<a href="${url}">${name}</a>`;
                } else {
                    return name;
                }
            }
            Layout.fillWidth: true
            Layout.preferredWidth: 1
            onLinkActivated: Qt.openUrlExternally(url)
        }

        UM.Label
        {
            text: description
            Layout.fillWidth: true
            Layout.preferredWidth: 2
        }

        UM.Label
        {
            text:
            {
                if (license_full !== "")
                {
                    return `<a href="license_full">${license}</a>`;
                }
                else
                {
                    return license;
                }
            }
            Layout.fillWidth: true
            Layout.preferredWidth: 1

            Component
            {
                id: componentLicenseDialog

                LicenseDialog { }
            }

            onLinkActivated:
            {
                var license_dialog = componentLicenseDialog.createObject(base, {name: name, version: version, license: license_full});
                license_dialog.open();
            }
        }

        UM.Label
        {
            text: version
            Layout.fillWidth: true
            Layout.preferredWidth: 1
        }
    }

    Flickable
    {
        id: scroll
        anchors.fill: parent
        ScrollBar.vertical: UM.ScrollBar {
            visible: scroll.contentHeight > height
        }
        contentHeight: content.height
        clip: true

        Column
        {
            id: content
            spacing: UM.Theme.getSize("default_margin").height
            width: parent.width

            UM.Label
            {
                text: catalog.i18nc("@label", "End-to-end solution for fused filament 3D printing.")
                font: UM.Theme.getFont("system")
                wrapMode: Text.WordWrap
            }

            UM.Label
            {
                text: catalog.i18nc("@info:credit", "Cura is developed by UltiMaker in cooperation with the community.\nCura proudly uses the following open source projects:")
                font: UM.Theme.getFont("system")
                wrapMode: Text.WordWrap
            }

            Column
            {
                visible: showDefaultDependencies
                width: parent.width
                spacing: UM.Theme.getSize("narrow_margin").height

                Repeater
                {
                    width: parent.width

                    delegate: Loader
                    {
                        sourceComponent: dependency_row
                        width: parent.width
                        property string name: modelData.name
                        property string description: modelData.summary
                        property string license: modelData.license
                        property string license_full: modelData.license_full
                        property string url: modelData.sources_url
                        property string version: modelData.version
                    }

                    property var dependencies_model: Cura.OpenSourceDependenciesModel {}
                    model: dependencies_model.dependencies
                }
            }

            UM.Label
            {
                visible: !showDefaultDependencies
                text: "Conan Installs"
                font: UM.Theme.getFont("large_bold")
            }

            Column
            {
                visible: !showDefaultDependencies
                width: parent.width

                Repeater
                {
                    width: parent.width
                    model: Object
                        .entries(CuraApplication.conanInstalls)
                        .map(([name, { version }]) => ({ name, version }))
                    delegate: Loader
                    {
                        sourceComponent: dependency_row
                        width: parent.width
                        property string name: modelData.name
                        property string version: modelData.version
                        property string license: ""
                        property string license_full: ""
                        property string url: ""
                        property string description: ""
                    }
                }
            }

            UM.Label
            {
                visible: !showDefaultDependencies
                text: "Python Installs"
                font: UM.Theme.getFont("large_bold")
            }

            Column
            {
                width: parent.width
                visible: !showDefaultDependencies

                Repeater
                {
                    delegate: Loader
                    {
                        sourceComponent: dependency_row
                        width: parent.width
                        property string name: modelData.name
                        property string version: modelData.version
                        property string license: ""
                        property string license_full: ""
                        property string url: ""
                        property string description: ""
                    }
                    width: parent.width
                    model: Object
                        .entries(CuraApplication.pythonInstalls)
                        .map(([name, { version }]) => ({ name, version }))
                }
            }
        }
    }

    rightButtons: Cura.TertiaryButton
    {
        id: closeButton
        text: catalog.i18nc("@action:button", "Close")
        onClicked: reject()
    }
}
