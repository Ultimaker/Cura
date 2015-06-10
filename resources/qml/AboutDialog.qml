// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Window 2.1

import UM 1.0 as UM

UM.Dialog {
    id: base

    //: About dialog title
    title: qsTr("About Cura")
    minimumWidth: 400
    minimumHeight: 300

    Image {
        id: logo
        width: parent.width * 0.75
        height: width * (1/4.25)

        source: UM.Theme.images.logo

        sourceSize.width: width
        sourceSize.height: height
        anchors.centerIn: parent
        anchors.verticalCenterOffset : -(height * 0.5)
    }

    Label {
        id: version

        text: "Cura 15.06 Beta"
        font: UM.Theme.fonts.large
        anchors.horizontalCenter : logo.horizontalCenter
        anchors.horizontalCenterOffset : (logo.width * 0.25)
        anchors.top: logo.bottom
        anchors.topMargin : 5
    }

    Label {
        id: description
        width: parent.width

        //: About dialog application description
        text: qsTr("End-to-end solution for fused filament 3D printing.")
        wrapMode: Text.WordWrap
        anchors.top: version.bottom
        anchors.topMargin : 10
    }

    Label {
        id: author_note
        width: parent.width

        //: About dialog application author note
        text: qsTr("Cura has been developed by Ultimaker B.V. in cooperation with the community.")
        wrapMode: Text.WordWrap
        anchors.top: description.bottom
    }

    rightButtons: Button {
        //: Close about dialog button
        text: qsTr("Close");

        onClicked: base.visible = false;
    }
}

