// Copyright (c) 2018 Ultimaker B.V.
// Toolbox is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Dialogs 1.1
import QtQuick.Window 2.2
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4

// TODO: Switch to QtQuick.Controls 2.x and remove QtQuick.Controls.Styles

import UM 1.1 as UM
import Cura 1.6 as Cura


UM.Dialog{
    visible: true
    title: "Changes from your account"
    Label{
        text: "Some text here"
        height: 50
    }
Rectangle
{
    id: compatibleRectangle
    width: parent.width
    height: 300
    Label{
        text: "Some text here"
        height: 50
    }



    // Compatible packages
    Column{
        id: compatibleColumn
        anchors.fill: parent
        spacing: 2

        Repeater{
            model: toolbox.subscribedPackagesModel
            delegate: Rectangle{
                id: someRect
                width: parent.width
                height: 50
                border.color: "black"
                Image{
                    source: model.icon_url || "../../images/logobot.svg"
                    width: 50
                    height: parent.height
                    //anchors.left: parent.left
                    //anchors.right: packageName.left
                    anchors.rightMargin: 20
                }
                Text{
                    id: packageName
                    text: model.name + " (Compatible: " + model.is_compatible + ")"
                    anchors.centerIn: parent
                }
                MouseArea{
                    anchors.fill: parent
                    onClicked: {
                        console.log("Clicked!")
                    }
                }

            }
        }
    }
}



}
