import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1
import QtQuick.Window 2.1

import UM 1.0 as UM

UM.Dialog {
    id: base

    //: About dialog title
    title: qsTr("About Cura");

    ColumnLayout {
        anchors.fill: parent;

        Item {
            Layout.fillWidth: true;
            Layout.fillHeight: true;
        }

        Image {
            Layout.alignment: Qt.AlignHCenter;
            Layout.preferredWidth: parent.width * 0.75;
            Layout.preferredHeight: width * (1/4.25);

            source: UM.Theme.images.logo;

            sourceSize.width: width;
            sourceSize.height: height;
        }

        Label {
            Layout.alignment: Qt.AlignHCenter;

            text: "Cura 15.06 Beta";
            font: UM.Theme.fonts.large;
        }

        Label {
            //: About dialog application description
            text: qsTr("End-to-end solution for fused filament 3D printing.")
        }

        Label {
            //: About dialog application author note
            text: qsTr("Cura has been developed by Ultimaker B.V. in cooperation with the community.")
        }

        Item {
            Layout.fillWidth: true;
            Layout.fillHeight: true;
        }
    }

    rightButtons: Button {
        //: Close about dialog button
        text: qsTr("Close");

        onClicked: base.visible = false;
    }
}

