// Copyright (c) 2018 Ultimaker B.V.
// Toolbox is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Dialogs 1.1
import QtQuick.Window 2.2
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import UM 1.1 as UM

Window {
    // title: catalog.i18nc("@title:tab", "Plugins");
    width: 360 * screenScaleFactor
    height: 120 * screenScaleFactor
    minimumWidth: 360 * screenScaleFactor
    minimumHeight: 120 * screenScaleFactor
    color: UM.Theme.getColor("sidebar")
    property var message;

    Text {
        id: message
        anchors {
            left: parent.left
            leftMargin: UM.Theme.getSize("default_margin").width
            top: parent.top
            topMargin: UM.Theme.getSize("default_margin").height
        }
        text: restartDialog.message != null ? restartDialog.message : ""
    }
    Button {
        id: laterButton
        text: "Later"
        onClicked: restartDialog.close();
        anchors {
            left: parent.left
            leftMargin: UM.Theme.getSize("default_margin").width
            bottom: parent.bottom
            bottomMargin: UM.Theme.getSize("default_margin").height
        }
        style: ButtonStyle {
            background: Rectangle {
                color: "transparent"
                implicitWidth: 96
                implicitHeight: 30
                border {
                    width: 1
                    color: UM.Theme.getColor("lining")
                }
            }
            label: Text {
                verticalAlignment: Text.AlignVCenter
                color: UM.Theme.getColor("text")
                text: control.text
                horizontalAlignment: Text.AlignHCenter
            }
        }
    }


    Button {
        id: restartButton
        text: "Quit Cura"
        anchors {
            right: parent.right
            rightMargin: UM.Theme.getSize("default_margin").width
            bottom: parent.bottom
            bottomMargin: UM.Theme.getSize("default_margin").height
        }
        onClicked: manager.restart()
        style: ButtonStyle {
            background: Rectangle {
                implicitWidth: 96
                implicitHeight: 30
                color: UM.Theme.getColor("primary")
            }
            label: Text {
                verticalAlignment: Text.AlignVCenter
                color: UM.Theme.getColor("button_text")
                font {
                    pixelSize: 13
                    bold: true
                }
                text: control.text
                horizontalAlignment: Text.AlignHCenter
            }
        }
    }
}
