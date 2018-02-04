// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Window 2.1

import UM 1.1 as UM

UM.Dialog
{
    id: base

    //: About dialog title
    title: catalog.i18nc("@title:window","About Cura")

    minimumWidth: 500 * screenScaleFactor
    minimumHeight: 650 * screenScaleFactor
    width: minimumWidth
    height: minimumHeight

    Image
    {
        id: logo
        width: (base.minimumWidth * 0.85) | 0
        height: (width * (1/4.25)) | 0

        source: UM.Theme.getImage("logo")

        sourceSize.width: width
        sourceSize.height: height
        anchors.top: parent.top
        anchors.topMargin: ((base.minimumWidth - width) / 2) | 0
        anchors.horizontalCenter: parent.horizontalCenter

        UM.I18nCatalog{id: catalog; name:"cura"}
    }

    Label
    {
        id: version

        text: catalog.i18nc("@label","version: %1").arg(UM.Application.version)
        font: UM.Theme.getFont("large")
        anchors.right : logo.right
        anchors.top: logo.bottom
        anchors.topMargin: (UM.Theme.getSize("default_margin").height / 2) | 0
    }

    Label
    {
        id: description
        width: parent.width

        //: About dialog application description
        text: catalog.i18nc("@label","End-to-end solution for fused filament 3D printing.")
        font: UM.Theme.getFont("system")
        wrapMode: Text.WordWrap
        anchors.top: version.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").height
    }

    Label
    {
        id: creditsNotes
        width: parent.width

        //: About dialog application author note
        text: catalog.i18nc("@info:credit","Cura is developed by Ultimaker B.V. in cooperation with the community.\nCura proudly uses the following open source projects:")
        font: UM.Theme.getFont("system")
        wrapMode: Text.WordWrap
        anchors.top: description.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").height
    }

    ScrollView
    {
        anchors.top: creditsNotes.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").height

        width: parent.width
        height: base.height - y - (2 * UM.Theme.getSize("default_margin").height + closeButton.height)

        ListView
        {
            id: projectsList

            width: parent.width

            delegate: Row
            {
                Label
                {
                    text: "<a href='%1' title='%2'>%2</a>".arg(model.url).arg(model.name)
                    width: (projectsList.width * 0.25) | 0
                    elide: Text.ElideRight
                    onLinkActivated: Qt.openUrlExternally(link)
                }
                Label
                {
                    text: model.description
                    elide: Text.ElideRight
                    width: (projectsList.width * 0.6) | 0
                }
                Label
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
                projectsModel.append({ name:"Cura", description: catalog.i18nc("@label", "Graphical user interface"), license: "LGPLv3", url: "https://github.com/Ultimaker/Cura" });
                projectsModel.append({ name:"Uranium", description: catalog.i18nc("@label", "Application framework"), license: "LGPLv3", url: "https://github.com/Ultimaker/Uranium" });
                projectsModel.append({ name:"CuraEngine", description: catalog.i18nc("@label", "GCode generator"), license: "AGPLv3", url: "https://github.com/Ultimaker/CuraEngine" });
                projectsModel.append({ name:"libArcus", description: catalog.i18nc("@label", "Interprocess communication library"), license: "LGPLv3", url: "https://github.com/Ultimaker/libArcus" });

                projectsModel.append({ name:"Python", description: catalog.i18nc("@label", "Programming language"), license: "Python", url: "http://python.org/" });
                projectsModel.append({ name:"Qt5", description: catalog.i18nc("@label", "GUI framework"), license: "LGPLv3", url: "https://www.qt.io/" });
                projectsModel.append({ name:"PyQt", description: catalog.i18nc("@label", "GUI framework bindings"), license: "GPL", url: "https://riverbankcomputing.com/software/pyqt" });
                projectsModel.append({ name:"SIP", description: catalog.i18nc("@label", "C/C++ Binding library"), license: "GPL", url: "https://riverbankcomputing.com/software/sip" });
                projectsModel.append({ name:"Protobuf", description: catalog.i18nc("@label", "Data interchange format"), license: "BSD", url: "https://developers.google.com/protocol-buffers" });
                projectsModel.append({ name:"SciPy", description: catalog.i18nc("@label", "Support library for scientific computing"), license: "BSD-new", url: "https://www.scipy.org/" });
                projectsModel.append({ name:"NumPy", description: catalog.i18nc("@label", "Support library for faster math"), license: "BSD", url: "http://www.numpy.org/" });
                projectsModel.append({ name:"NumPy-STL", description: catalog.i18nc("@label", "Support library for handling STL files"), license: "BSD", url: "https://github.com/WoLpH/numpy-stl" });
                projectsModel.append({ name:"libSavitar", description: catalog.i18nc("@label", "Support library for handling 3MF files"), license: "LGPLv3", url: "https://github.com/ultimaker/libsavitar" });
                projectsModel.append({ name:"PySerial", description: catalog.i18nc("@label", "Serial communication library"), license: "Python", url: "http://pyserial.sourceforge.net/" });
                projectsModel.append({ name:"python-zeroconf", description: catalog.i18nc("@label", "ZeroConf discovery library"), license: "LGPL", url: "https://github.com/jstasiak/python-zeroconf" });
                projectsModel.append({ name:"Clipper", description: catalog.i18nc("@label", "Polygon clipping library"), license: "Boost", url: "http://www.angusj.com/delphi/clipper.php" });
                projectsModel.append({ name:"Requests", description: catalog.i18nc("@Label", "Python HTTP library"), license: "GPL", url: "http://docs.python-requests.org" });

                projectsModel.append({ name:"Open Sans", description: catalog.i18nc("@label", "Font"), license: "Apache 2.0", url: "https://fonts.google.com/specimen/Open+Sans" });
                projectsModel.append({ name:"Font-Awesome-SVG-PNG", description: catalog.i18nc("@label", "SVG icons"), license: "SIL OFL 1.1", url: "https://github.com/encharm/Font-Awesome-SVG-PNG" });
            }
        }
    }

    rightButtons: Button
    {
        //: Close about dialog button
        id: closeButton
        text: catalog.i18nc("@action:button","Close");

        onClicked: base.visible = false;
    }
}

