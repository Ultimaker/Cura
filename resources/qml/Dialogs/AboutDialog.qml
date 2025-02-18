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

                LicenseDialog
                {
                }
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
                        property string license_full: model.license_full
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
                        projectsModel.append({ name: "Cura", description: catalog.i18nc("@label Description for application component", "Graphical user interface"), license: "LGPLv3", license_full: "", url: "https://github.com/Ultimaker/Cura" });
                        projectsModel.append({ name: "Uranium", description: catalog.i18nc("@label Description for application component", "Application framework"), license: "LGPLv3", license_full: "", url: "https://github.com/Ultimaker/Uranium" });
                        projectsModel.append({ name: "CuraEngine", description: catalog.i18nc("@label Description for application component", "G-code generator"), license: "AGPLv3", license_full: "", url: "https://github.com/Ultimaker/CuraEngine" });
                        projectsModel.append({ name: "libArcus", description: catalog.i18nc("@label Description for application component", "Interprocess communication library"), license: "LGPLv3", license_full: "", url: "https://github.com/Ultimaker/libArcus" });
                        projectsModel.append({ name: "pynest2d", description: catalog.i18nc("@label Description for application component", "Python bindings for libnest2d"), license: "LGPL", license_full: "", url: "https://github.com/Ultimaker/pynest2d" });
                        projectsModel.append({ name: "libnest2d", description: catalog.i18nc("@label Description for application component", "Polygon packing library, developed by Prusa Research"), license: "LGPL", license_full: "", url: "https://github.com/tamasmeszaros/libnest2d" });
                        projectsModel.append({ name: "libSavitar", description: catalog.i18nc("@label Description for application component", "Support library for handling 3MF files"), license: "LGPLv3", license_full: "", url: "https://github.com/ultimaker/libsavitar" });
                        projectsModel.append({ name: "libCharon", description: catalog.i18nc("@label Description for application component", "Support library for file metadata and streaming"), license: "LGPLv3", license_full: "", url: "https://github.com/ultimaker/libcharon" });

                        //Direct dependencies of the front-end.
                        projectsModel.append({ name: "Python", description: catalog.i18nc("@label Description for application dependency", "Programming language"), license: "Python", license_full: "", url: "http://python.org/" });
                        projectsModel.append({ name: "Qt6", description: catalog.i18nc("@label Description for application dependency", "GUI framework"), license: "LGPLv3", license_full: "                   GNU LESSER GENERAL PUBLIC LICENSE\n" +
                                "                       Version 3, 29 June 2007\n" +
                                "\n" +
                                " Copyright (C) 2007 Free Software Foundation, Inc. <http://fsf.org/>\n" +
                                " Everyone is permitted to copy and distribute verbatim copies\n" +
                                " of this license document, but changing it is not allowed.\n" +
                                "\n" +
                                "\n" +
                                "  This version of the GNU Lesser General Public License incorporates\n" +
                                "the terms and conditions of version 3 of the GNU General Public\n" +
                                "License, supplemented by the additional permissions listed below.\n" +
                                "\n" +
                                "  0. Additional Definitions.\n" +
                                "\n" +
                                "  As used herein, \"this License\" refers to version 3 of the GNU Lesser\n" +
                                "General Public License, and the \"GNU GPL\" refers to version 3 of the GNU\n" +
                                "General Public License.\n" +
                                "\n" +
                                "  \"The Library\" refers to a covered work governed by this License,\n" +
                                "other than an Application or a Combined Work as defined below.\n" +
                                "\n" +
                                "  An \"Application\" is any work that makes use of an interface provided\n" +
                                "by the Library, but which is not otherwise based on the Library.\n" +
                                "Defining a subclass of a class defined by the Library is deemed a mode\n" +
                                "of using an interface provided by the Library.\n" +
                                "\n" +
                                "  A \"Combined Work\" is a work produced by combining or linking an\n" +
                                "Application with the Library.  The particular version of the Library\n" +
                                "with which the Combined Work was made is also called the \"Linked\n" +
                                "Version\".\n" +
                                "\n" +
                                "  The \"Minimal Corresponding Source\" for a Combined Work means the\n" +
                                "Corresponding Source for the Combined Work, excluding any source code\n" +
                                "for portions of the Combined Work that, considered in isolation, are\n" +
                                "based on the Application, and not on the Linked Version.\n" +
                                "\n" +
                                "  The \"Corresponding Application Code\" for a Combined Work means the\n" +
                                "object code and/or source code for the Application, including any data\n" +
                                "and utility programs needed for reproducing the Combined Work from the\n" +
                                "Application, but excluding the System Libraries of the Combined Work.\n" +
                                "\n" +
                                "  1. Exception to Section 3 of the GNU GPL.\n" +
                                "\n" +
                                "  You may convey a covered work under sections 3 and 4 of this License\n" +
                                "without being bound by section 3 of the GNU GPL.\n" +
                                "\n" +
                                "  2. Conveying Modified Versions.\n" +
                                "\n" +
                                "  If you modify a copy of the Library, and, in your modifications, a\n" +
                                "facility refers to a function or data to be supplied by an Application\n" +
                                "that uses the facility (other than as an argument passed when the\n" +
                                "facility is invoked), then you may convey a copy of the modified\n" +
                                "version:\n" +
                                "\n" +
                                "   a) under this License, provided that you make a good faith effort to\n" +
                                "   ensure that, in the event an Application does not supply the\n" +
                                "   function or data, the facility still operates, and performs\n" +
                                "   whatever part of its purpose remains meaningful, or\n" +
                                "\n" +
                                "   b) under the GNU GPL, with none of the additional permissions of\n" +
                                "   this License applicable to that copy.\n" +
                                "\n" +
                                "  3. Object Code Incorporating Material from Library Header Files.\n" +
                                "\n" +
                                "  The object code form of an Application may incorporate material from\n" +
                                "a header file that is part of the Library.  You may convey such object\n" +
                                "code under terms of your choice, provided that, if the incorporated\n" +
                                "material is not limited to numerical parameters, data structure\n" +
                                "layouts and accessors, or small macros, inline functions and templates\n" +
                                "(ten or fewer lines in length), you do both of the following:\n" +
                                "\n" +
                                "   a) Give prominent notice with each copy of the object code that the\n" +
                                "   Library is used in it and that the Library and its use are\n" +
                                "   covered by this License.\n" +
                                "\n" +
                                "   b) Accompany the object code with a copy of the GNU GPL and this license\n" +
                                "   document.\n" +
                                "\n" +
                                "  4. Combined Works.\n" +
                                "\n" +
                                "  You may convey a Combined Work under terms of your choice that,\n" +
                                "taken together, effectively do not restrict modification of the\n" +
                                "portions of the Library contained in the Combined Work and reverse\n" +
                                "engineering for debugging such modifications, if you also do each of\n" +
                                "the following:\n" +
                                "\n" +
                                "   a) Give prominent notice with each copy of the Combined Work that\n" +
                                "   the Library is used in it and that the Library and its use are\n" +
                                "   covered by this License.\n" +
                                "\n" +
                                "   b) Accompany the Combined Work with a copy of the GNU GPL and this license\n" +
                                "   document.\n" +
                                "\n" +
                                "   c) For a Combined Work that displays copyright notices during\n" +
                                "   execution, include the copyright notice for the Library among\n" +
                                "   these notices, as well as a reference directing the user to the\n" +
                                "   copies of the GNU GPL and this license document.\n" +
                                "\n" +
                                "   d) Do one of the following:\n" +
                                "\n" +
                                "       0) Convey the Minimal Corresponding Source under the terms of this\n" +
                                "       License, and the Corresponding Application Code in a form\n" +
                                "       suitable for, and under terms that permit, the user to\n" +
                                "       recombine or relink the Application with a modified version of\n" +
                                "       the Linked Version to produce a modified Combined Work, in the\n" +
                                "       manner specified by section 6 of the GNU GPL for conveying\n" +
                                "       Corresponding Source.\n" +
                                "\n" +
                                "       1) Use a suitable shared library mechanism for linking with the\n" +
                                "       Library.  A suitable mechanism is one that (a) uses at run time\n" +
                                "       a copy of the Library already present on the user's computer\n" +
                                "       system, and (b) will operate properly with a modified version\n" +
                                "       of the Library that is interface-compatible with the Linked\n" +
                                "       Version.\n" +
                                "\n" +
                                "   e) Provide Installation Information, but only if you would otherwise\n" +
                                "   be required to provide such information under section 6 of the\n" +
                                "   GNU GPL, and only to the extent that such information is\n" +
                                "   necessary to install and execute a modified version of the\n" +
                                "   Combined Work produced by recombining or relinking the\n" +
                                "   Application with a modified version of the Linked Version. (If\n" +
                                "   you use option 4d0, the Installation Information must accompany\n" +
                                "   the Minimal Corresponding Source and Corresponding Application\n" +
                                "   Code. If you use option 4d1, you must provide the Installation\n" +
                                "   Information in the manner specified by section 6 of the GNU GPL\n" +
                                "   for conveying Corresponding Source.)\n" +
                                "\n" +
                                "  5. Combined Libraries.\n" +
                                "\n" +
                                "  You may place library facilities that are a work based on the\n" +
                                "Library side by side in a single library together with other library\n" +
                                "facilities that are not Applications and are not covered by this\n" +
                                "License, and convey such a combined library under terms of your\n" +
                                "choice, if you do both of the following:\n" +
                                "\n" +
                                "   a) Accompany the combined library with a copy of the same work based\n" +
                                "   on the Library, uncombined with any other library facilities,\n" +
                                "   conveyed under the terms of this License.\n" +
                                "\n" +
                                "   b) Give prominent notice with the combined library that part of it\n" +
                                "   is a work based on the Library, and explaining where to find the\n" +
                                "   accompanying uncombined form of the same work.\n" +
                                "\n" +
                                "  6. Revised Versions of the GNU Lesser General Public License.\n" +
                                "\n" +
                                "  The Free Software Foundation may publish revised and/or new versions\n" +
                                "of the GNU Lesser General Public License from time to time. Such new\n" +
                                "versions will be similar in spirit to the present version, but may\n" +
                                "differ in detail to address new problems or concerns.\n" +
                                "\n" +
                                "  Each version is given a distinguishing version number. If the\n" +
                                "Library as you received it specifies that a certain numbered version\n" +
                                "of the GNU Lesser General Public License \"or any later version\"\n" +
                                "applies to it, you have the option of following the terms and\n" +
                                "conditions either of that published version or of any later version\n" +
                                "published by the Free Software Foundation. If the Library as you\n" +
                                "received it does not specify a version number of the GNU Lesser\n" +
                                "General Public License, you may choose any version of the GNU Lesser\n" +
                                "General Public License ever published by the Free Software Foundation.\n" +
                                "\n" +
                                "  If the Library as you received it specifies that a proxy can decide\n" +
                                "whether future versions of the GNU Lesser General Public License shall\n" +
                                "apply, that proxy's public statement of acceptance of any version is\n" +
                                "permanent authorization for you to choose that version for the\n" +
                                "Library.\n", url: "https://code.qt.io/cgit/qt/qtbase.git/" });
                        projectsModel.append({ name: "PyQt", description: catalog.i18nc("@label Description for application dependency", "GUI framework bindings"), license: "GPL", license_full: "", url: "https://riverbankcomputing.com/software/pyqt" });
                        projectsModel.append({ name: "SIP", description: catalog.i18nc("@label Description for application dependency", "C/C++ Binding library"), license: "GPL", license_full: "", url: "https://riverbankcomputing.com/software/sip" });
                        projectsModel.append({ name: "Protobuf", description: catalog.i18nc("@label Description for application dependency", "Data interchange format"), license: "BSD", license_full: "", url: "https://developers.google.com/protocol-buffers" });
                        projectsModel.append({ name: "Noto Sans", description: catalog.i18nc("@label", "Font"), license: "Apache 2.0", license_full: "", url: "https://www.google.com/get/noto/" });

                        //CuraEngine's dependencies.
                        projectsModel.append({ name: "Clipper", description: catalog.i18nc("@label Description for application dependency", "Polygon clipping library"), license: "Boost", license_full: "", url: "http://www.angusj.com/delphi/clipper.php" });
                        projectsModel.append({ name: "RapidJSON", description: catalog.i18nc("@label Description for application dependency", "JSON parser"), license: "MIT", license_full: "", url: "https://rapidjson.org/" });
                        projectsModel.append({ name: "STB", description: catalog.i18nc("@label Description for application dependency", "Utility functions, including an image loader"), license: "Public Domain", license_full: "", url: "https://github.com/nothings/stb" });
                        projectsModel.append({ name: "Boost", description: catalog.i18nc("@label Description for application dependency", "Utility library, including Voronoi generation"), license: "Boost", license_full: "", url: "https://www.boost.org/" });

                        //Python modules.
                        projectsModel.append({ name: "Certifi", description: catalog.i18nc("@label Description for application dependency", "Root Certificates for validating SSL trustworthiness"), license: "MPL", license_full: "", url: "https://github.com/certifi/python-certifi" });
                        projectsModel.append({ name: "Cryptography", description: catalog.i18nc("@label Description for application dependency", "Root Certificates for validating SSL trustworthiness"), license: "APACHE and BSD", license_full: "", url: "https://cryptography.io/" });
                        projectsModel.append({ name: "Future", description: catalog.i18nc("@label Description for application dependency", "Compatibility between Python 2 and 3"), license: "MIT", license_full: "", url: "https://python-future.org/" });
                        projectsModel.append({ name: "keyring", description: catalog.i18nc("@label Description for application dependency", "Support library for system keyring access"), license: "MIT", license_full: "", url: "https://github.com/jaraco/keyring" });
                        projectsModel.append({ name: "NumPy", description: catalog.i18nc("@label Description for application dependency", "Support library for faster math"), license: "BSD", license_full: "", url: "http://www.numpy.org/" });
                        projectsModel.append({ name: "NumPy-STL", description: catalog.i18nc("@label Description for application dependency", "Support library for handling STL files"), license: "BSD", license_full: "", url: "https://github.com/WoLpH/numpy-stl" });
                        projectsModel.append({ name: "PyClipper", description: catalog.i18nc("@label Description for application dependency", "Python bindings for Clipper"), license: "MIT", license_full: "", url: "https://github.com/fonttools/pyclipper" });
                        projectsModel.append({ name: "PySerial", description: catalog.i18nc("@label Description for application dependency", "Serial communication library"), license: "Python", license_full: "", url: "http://pyserial.sourceforge.net/" });
                        projectsModel.append({ name: "SciPy", description: catalog.i18nc("@label Description for application dependency", "Support library for scientific computing"), license: "BSD-new", license_full: "", url: "https://www.scipy.org/" });
                        projectsModel.append({ name: "Sentry", description: catalog.i18nc("@Label Description for application dependency", "Python Error tracking library"), license: "BSD 2-Clause 'Simplified'", license_full: "", url: "https://sentry.io/for/python/" });
                        projectsModel.append({ name: "Trimesh", description: catalog.i18nc("@label Description for application dependency", "Support library for handling triangular meshes"), license: "MIT", license_full: "", url: "https://trimsh.org" });
                        projectsModel.append({ name: "python-zeroconf", description: catalog.i18nc("@label Description for application dependency", "ZeroConf discovery library"), license: "LGPL", license_full: "", url: "https://github.com/jstasiak/python-zeroconf" });

                        //Building/packaging.
                        projectsModel.append({ name: "CMake", description: catalog.i18nc("@label Description for development tool", "Universal build system configuration"), license: "BSD 3-Clause", license_full: "", url: "https://cmake.org/" });
                        projectsModel.append({ name: "Conan", description: catalog.i18nc("@label Description for development tool", "Dependency and package manager"), license: "MIT", license_full: "", url: "https://conan.io/" });
                        projectsModel.append({ name: "Pyinstaller", description: catalog.i18nc("@label Description for development tool", "Packaging Python-applications"), license: "GPLv2", license_full: "", url: "https://pyinstaller.org/" });
                        projectsModel.append({ name: "AppImageKit", description: catalog.i18nc("@label Description for development tool", "Linux cross-distribution application deployment"), license: "MIT", license_full: "", url: "https://github.com/AppImage/AppImageKit" });
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
