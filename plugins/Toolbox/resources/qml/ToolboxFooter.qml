// Copyright (c) 2018 Ultimaker B.V.
// PluginBrowser is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Dialogs 1.1
import QtQuick.Window 2.2
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4

// TODO: Switch to QtQuick.Controls 2.x and remove QtQuick.Controls.Styles

import UM 1.1 as UM

Rectangle {
    width: parent.width
    height: UM.Theme.getSize("base_unit").height * 4
    color: "transparent"
    anchors.bottom: parent.bottom

    Label {
        visible: manager.restartRequired
        text: "You will need to restart Cura before changes in plugins have effect."
        height: 30
        verticalAlignment: Text.AlignVCenter
    }
    Button {
        id: restartChangedButton
        text: "Quit Cura"
        anchors.right: closeButton.left
        anchors.rightMargin: UM.Theme.getSize("default_margin").width
        visible: manager.restartRequired
        iconName: "dialog-restart"
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

    Button {
        id: closeButton
        text: catalog.i18nc("@action:button", "Close")
        iconName: "dialog-close"
        onClicked: {
            if ( manager.isDownloading ) {
                manager.cancelDownload()
            }
            base.close();
        }
        anchors
        {
            top: parent.top
            topMargin: UM.Theme.getSize("default_margin").height
            right: parent.right
            rightMargin: UM.Theme.getSize("default_margin").height
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
}
