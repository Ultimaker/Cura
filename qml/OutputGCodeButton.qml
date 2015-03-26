import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1

import UM 1.0 as UM

Rectangle {
    id: base;

    color: UM.Theme.colors.primary;

    signal saveRequested();
    signal saveToSDRequested();

    Image {
        id: icon;

        anchors.left: parent.left;
        anchors.top: parent.top;
        anchors.bottom: parent.bottom;

        width: height;

        sourceSize.width: width;
        sourceSize.height: height;

        source: UM.Theme.icons.save;
    }

    Label {
        id: label;
        anchors.verticalCenter: parent.verticalCenter;
        anchors.left: icon.left;
        anchors.right: parent.right;
        horizontalAlignment: Text.AlignHCenter;
        font.pointSize: UM.Styles.largeTextSize;
        color: "white";

        //: Save file to disk button
        text: qsTr("Save");
    }

    MouseArea {
        anchors.fill: parent;

        onClicked: {
            switch(base.state) {
                case 'sdcard':
                    base.saveToSDRequested();
                    break;
                default:
                    base.saveRequested();
                    break;
            }
        }
    }

    states: [
        State {
            name: 'sdcard';
            when: Printer.removableDrives.length > 0;
            PropertyChanges {
                target: label;
                //: Write to SD card button
                text: qsTr("Write to SD");
            }
            PropertyChanges { target: iconImage; source: UM.Resources.getIcon('sdcard.png'); }
        },
        State {
            name: 'usb';
            PropertyChanges {
                target: label
                //: Send print over USB button
                text: qsTr("Send over USB");
            }
            PropertyChanges { target: iconImage; source: UM.Resources.getIcon('usb.png'); }
        }
    ]

    transitions: [
        Transition {
            SequentialAnimation {
                ParallelAnimation {
                    NumberAnimation { target: label; property: 'opacity'; to: 0; duration: 250; }
                    NumberAnimation { target: iconImage; property: 'opacity'; to: 0; duration: 250; }
                }
                PropertyAction { target: label; property: 'text'; }
                PropertyAction { target: iconImage; property: 'source'; }
                ParallelAnimation {
                    NumberAnimation { target: label; property: 'opacity'; to: 1; duration: 250; }
                    NumberAnimation { target: iconImage; property: 'opacity'; to: 1; duration: 250; }
                }
            }
        }
    ]
}
