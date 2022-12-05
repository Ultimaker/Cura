// Copyright (c) 2022 UltiMaker
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 2.9

import UM 1.5 as UM
import Cura 1.5 as Cura

UM.Dialog
{
    id: base

    //: About dialog title
    title: catalog.i18nc("@title:window The argument is the application name.", "About %1").arg(CuraApplication.applicationDisplayName)

    minimumWidth: 500 * screenScaleFactor
    minimumHeight: 700 * screenScaleFactor
    width: minimumWidth
    height: minimumHeight

    backgroundColor: UM.Theme.getColor("main_background")

    Rectangle
    {
        id: header
        width: parent.width + 2 * margin // margin from Dialog.qml
        height: childrenRect.height + topPadding

        anchors.top: parent.top
        anchors.topMargin: -margin
        anchors.horizontalCenter: parent.horizontalCenter

        property real topPadding: UM.Theme.getSize("wide_margin").height

        color: UM.Theme.getColor("main_window_header_background")

        Image
        {
            id: logo
            width: (base.minimumWidth * 0.85) | 0
            height: (width * (UM.Theme.getSize("logo").height / UM.Theme.getSize("logo").width)) | 0
            source: UM.Theme.getImage("logo")
            sourceSize.width: width
            sourceSize.height: height
            fillMode: Image.PreserveAspectFit

            anchors.top: parent.top
            anchors.topMargin: parent.topPadding
            anchors.horizontalCenter: parent.horizontalCenter

            UM.I18nCatalog{id: catalog; name: "cura"}
        }

        UM.Label
        {
            id: version

            text: catalog.i18nc("@label","version: %1").arg(UM.Application.version)
            font: UM.Theme.getFont("large_bold")
            color: UM.Theme.getColor("button_text")
            anchors.right : logo.right
            anchors.top: logo.bottom
            anchors.topMargin: (UM.Theme.getSize("default_margin").height / 2) | 0
        }
    }

    UM.Label
    {
        id: description
        width: parent.width

        //: About dialog application description
        text: catalog.i18nc("@label","End-to-end solution for fused filament 3D printing.")
        font: UM.Theme.getFont("system")
        wrapMode: Text.WordWrap
        anchors.top: header.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").height
    }

    UM.Label
    {
        id: creditsNotes
        width: parent.width

        //: About dialog application author note
        text: catalog.i18nc("@info:credit","Cura is developed by UltiMaker in cooperation with the community.\nCura proudly uses the following open source projects:")
        font: UM.Theme.getFont("system")
        wrapMode: Text.WordWrap
        anchors.top: description.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").height
    }

    ListView
    {
        id: projectsList
        anchors.top: creditsNotes.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").height
        width: parent.width
        height: base.height - y - (2 * UM.Theme.getSize("default_margin").height + closeButton.height)

        ScrollBar.vertical: UM.ScrollBar
        {
            id: projectsListScrollBar
        }

        delegate: Row
        {
            spacing: UM.Theme.getSize("narrow_margin").width
            UM.Label
            {
                text: "<a href='%1' title='%2'>%2</a>".arg(model.url).arg(model.name)
                width: (projectsList.width * 0.25) | 0
                elide: Text.ElideRight
                onLinkActivated: Qt.openUrlExternally(link)
            }
            UM.Label
            {
                text: model.description
                elide: Text.ElideRight
                width: ((projectsList.width * 0.6) | 0) - parent.spacing * 2 - projectsListScrollBar.width
            }
            UM.Label
            {
                text: model.license
                elide: Text.ElideRight
                width: (projectsList.width * 0.15) | 0
            }
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

    rightButtons: Cura.TertiaryButton
    {
        //: Close about dialog button
        id: closeButton
        text: catalog.i18nc("@action:button", "Close")
        onClicked: reject()
    }
}
