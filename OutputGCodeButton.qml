import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1

import UM 1.0 as UM

Rectangle {
    id: base;

    color: UM.Theme.primaryColor;
    border.width: 1;
    border.color: UM.Theme.borderColor;

    signal saveRequested();

    Label {
        id: label;
        anchors.verticalCenter: parent.verticalCenter;
        anchors.left: parent.left;
        anchors.right: icon.left;
        horizontalAlignment: Text.AlignHCenter;
        font.pointSize: UM.Theme.largeTextSize;
        color: "white";

        //: Save file to disk button
        text: qsTr("Save");
    }

    Rectangle {
        id: icon;

        anchors.right: parent.right;
        anchors.top: parent.top;
        anchors.bottom: parent.bottom;
        anchors.margins: 1;

        color: "white";

        width: height;

        Rectangle {
            anchors { left: parent.left; top: parent.top; bottom: parent.bottom; }
            width: 1;
            color: UM.Theme.borderColor;
        }

        UM.RecolorImage { id: iconImage; anchors.centerIn: parent; width: 32; height: 32; source: UM.Resources.getIcon('save.png'); color: '#000'; }
    }

    MouseArea {
        anchors.fill: parent;

        onClicked: {
            switch(base.state) {
                case 'sdcard':
                    base.state = 'usb';
                    break;
                case 'usb':
                    base.state = '';
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
            //: Write to SD card button
            PropertyChanges { target: label; text: qsTr("Write to SD"); }
            PropertyChanges { target: iconImage; source: UM.Resources.getIcon('sdcard.png'); }
        },
        State {
            name: 'usb';
            //: Send print over USB button
            PropertyChanges { target: label; text: qsTr("Send over USB"); }
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
