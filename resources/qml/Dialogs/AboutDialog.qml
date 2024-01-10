// Copyright (c) 2023 UltiMaker
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

    minimumWidth: 500 * screenScaleFactor
    minimumHeight: 700 * screenScaleFactor
    width: minimumWidth
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
            visible: text !== ""
            Layout.fillWidth: true
            Layout.preferredWidth: 1
            onLinkActivated: Qt.openUrlExternally(url)
        }

        UM.Label
        {
            text: description
            visible: text !== ""
            Layout.fillWidth: true
            Layout.preferredWidth: 2
        }

        UM.Label
        {
            text: license
            visible: text !== ""
            Layout.fillWidth: true
            Layout.preferredWidth: 1
        }

        UM.Label
        {
            text: version
            visible: text !== ""
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

                Repeater
                {
                    width: parent.width

                    delegate: Loader
                    {
                        sourceComponent: dependency_row
                        width: parent.width
                        property string name: model.name
                        property string description: model.description
                        property string license: model.license
                        property string url: model.url
                        property string version: ""
                    }

                    model: ListModel
                    {
                        id: projectsModel
                    }
                    Component.onCompleted:
                    {
                        //Do NOT add dependencies of our dependencies here, nor CI-dependencies!
                        //UltiMaker's own projects and forks.
                        projectsModel.append({ name: "Cura", description: catalog.i18nc("@label Description for application component", "Graphical user interface"), license: "LGPLv3", url: "https://github.com/Ultimaker/Cura" });
                        projectsModel.append({ name: "Uranium", description: catalog.i18nc("@label Description for application component", "Application framework"), license: "LGPLv3", url: "https://github.com/Ultimaker/Uranium" });
                        projectsModel.append({ name: "CuraEngine", description: catalog.i18nc("@label Description for application component", "G-code generator"), license: "AGPLv3", url: "https://github.com/Ultimaker/CuraEngine" });
                        projectsModel.append({ name: "libArcus", description: catalog.i18nc("@label Description for application component", "Interprocess communication library"), license: "LGPLv3", url: "https://github.com/Ultimaker/libArcus" });
                        projectsModel.append({ name: "pynest2d", description: catalog.i18nc("@label Description for application component", "Python bindings for libnest2d"), license: "LGPL", url: "https://github.com/Ultimaker/pynest2d" });
                        projectsModel.append({ name: "libnest2d", description: catalog.i18nc("@label Description for application component", "Polygon packing library, developed by Prusa Research"), license: "LGPL", url: "https://github.com/tamasmeszaros/libnest2d" });
                        projectsModel.append({ name: "libSavitar", description: catalog.i18nc("@label Description for application component", "Support library for handling 3MF files"), license: "LGPLv3", url: "https://github.com/ultimaker/libsavitar" });
                        projectsModel.append({ name: "libCharon", description: catalog.i18nc("@label Description for application component", "Support library for file metadata and streaming"), license: "LGPLv3", url: "https://github.com/ultimaker/libcharon" });

                        //Direct dependencies of the front-end.
                        projectsModel.append({ name: "Python", description: catalog.i18nc("@label Description for application dependency", "Programming language"), license: "Python", url: "http://python.org/" });
                        projectsModel.append({ name: "Qt6", description: catalog.i18nc("@label Description for application dependency", "GUI framework"), license: "LGPLv3", url: "https://www.qt.io/" });
                        projectsModel.append({ name: "PyQt", description: catalog.i18nc("@label Description for application dependency", "GUI framework bindings"), license: "GPL", url: "https://riverbankcomputing.com/software/pyqt" });
                        projectsModel.append({ name: "SIP", description: catalog.i18nc("@label Description for application dependency", "C/C++ Binding library"), license: "GPL", url: "https://riverbankcomputing.com/software/sip" });
                        projectsModel.append({ name: "Protobuf", description: catalog.i18nc("@label Description for application dependency", "Data interchange format"), license: "BSD", url: "https://developers.google.com/protocol-buffers" });
                        projectsModel.append({ name: "Noto Sans", description: catalog.i18nc("@label", "Font"), license: "Apache 2.0", url: "https://www.google.com/get/noto/" });

                        //CuraEngine's dependencies.
                        projectsModel.append({ name: "Clipper", description: catalog.i18nc("@label Description for application dependency", "Polygon clipping library"), license: "Boost", url: "http://www.angusj.com/delphi/clipper.php" });
                        projectsModel.append({ name: "RapidJSON", description: catalog.i18nc("@label Description for application dependency", "JSON parser"), license: "MIT", url: "https://rapidjson.org/" });
                        projectsModel.append({ name: "STB", description: catalog.i18nc("@label Description for application dependency", "Utility functions, including an image loader"), license: "Public Domain", url: "https://github.com/nothings/stb" });
                        projectsModel.append({ name: "Boost", description: catalog.i18nc("@label Description for application dependency", "Utility library, including Voronoi generation"), license: "Boost", url: "https://www.boost.org/" });

                        //Python modules.
                        projectsModel.append({ name: "Certifi", description: catalog.i18nc("@label Description for application dependency", "Root Certificates for validating SSL trustworthiness"), license: "MPL", url: "https://github.com/certifi/python-certifi" });
                        projectsModel.append({ name: "Cryptography", description: catalog.i18nc("@label Description for application dependency", "Root Certificates for validating SSL trustworthiness"), license: "APACHE and BSD", url: "https://cryptography.io/" });
                        projectsModel.append({ name: "Future", description: catalog.i18nc("@label Description for application dependency", "Compatibility between Python 2 and 3"), license: "MIT", url: "https://python-future.org/" });
                        projectsModel.append({ name: "keyring", description: catalog.i18nc("@label Description for application dependency", "Support library for system keyring access"), license: "MIT", url: "https://github.com/jaraco/keyring" });
                        projectsModel.append({ name: "NumPy", description: catalog.i18nc("@label Description for application dependency", "Support library for faster math"), license: "BSD", url: "http://www.numpy.org/" });
                        projectsModel.append({ name: "NumPy-STL", description: catalog.i18nc("@label Description for application dependency", "Support library for handling STL files"), license: "BSD", url: "https://github.com/WoLpH/numpy-stl" });
                        projectsModel.append({ name: "PyClipper", description: catalog.i18nc("@label Description for application dependency", "Python bindings for Clipper"), license: "MIT", url: "https://github.com/fonttools/pyclipper" });
                        projectsModel.append({ name: "PySerial", description: catalog.i18nc("@label Description for application dependency", "Serial communication library"), license: "Python", url: "http://pyserial.sourceforge.net/" });
                        projectsModel.append({ name: "SciPy", description: catalog.i18nc("@label Description for application dependency", "Support library for scientific computing"), license: "BSD-new", url: "https://www.scipy.org/" });
                        projectsModel.append({ name: "Sentry", description: catalog.i18nc("@Label Description for application dependency", "Python Error tracking library"), license: "BSD 2-Clause 'Simplified'", url: "https://sentry.io/for/python/" });
                        projectsModel.append({ name: "Trimesh", description: catalog.i18nc("@label Description for application dependency", "Support library for handling triangular meshes"), license: "MIT", url: "https://trimsh.org" });
                        projectsModel.append({ name: "python-zeroconf", description: catalog.i18nc("@label Description for application dependency", "ZeroConf discovery library"), license: "LGPL", url: "https://github.com/jstasiak/python-zeroconf" });

                        //Building/packaging.
                        projectsModel.append({ name: "CMake", description: catalog.i18nc("@label Description for development tool", "Universal build system configuration"), license: "BSD 3-Clause", url: "https://cmake.org/" });
                        projectsModel.append({ name: "Conan", description: catalog.i18nc("@label Description for development tool", "Dependency and package manager"), license: "MIT", url: "https://conan.io/" });
                        projectsModel.append({ name: "Pyinstaller", description: catalog.i18nc("@label Description for development tool", "Packaging Python-applications"), license: "GPLv2", url: "https://pyinstaller.org/" });
                        projectsModel.append({ name: "AppImageKit", description: catalog.i18nc("@label Description for development tool", "Linux cross-distribution application deployment"), license: "MIT", url: "https://github.com/AppImage/AppImageKit" });
                        projectsModel.append({ name: "NSIS", description: catalog.i18nc("@label Description for development tool", "Generating Windows installers"), license: "Zlib", url: "https://nsis.sourceforge.io/" });
                    }
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
