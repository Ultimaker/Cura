// Copyright (c) 2022 BCN3D B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.3 as UM
import Cura 1.1 as Cura


//
// This component contains first steps information
//
Item
{
    UM.I18nCatalog { id: catalog; name: "cura" }

    Label
    {
        id: titleLabel
        anchors.top: parent.top
        anchors.horizontalCenter: parent.horizontalCenter
        horizontalAlignment: Text.AlignHCenter
        text: catalog.i18nc("@label", "Tutorial: First Steps")
        color: UM.Theme.getColor("primary_button")
        font: UM.Theme.getFont("huge")
        renderType: Text.NativeRendering
    }

    // Area where the first steps contents can be put. videos, texts and such.
    Item
    {
        id: contentsArea

        anchors
        {
            top: titleLabel.bottom
            bottom: getStartedAplicationButton.top
            left: parent.left
            right: parent.right
            topMargin: UM.Theme.getSize("default_margin").width
        }

        Column
        {
            anchors.centerIn: parent
            width: parent.width

            spacing: UM.Theme.getSize("wide_margin").height

            Label
            {
                id: topLabel
                width: parent.width
                anchors.horizontalCenter: parent.horizontalCenter
                horizontalAlignment: Text.AlignHCenter
                text: catalog.i18nc("@text", "In this video we provide a clear and simple explanation on everything you'll need to know to start slicing your 3D models with BCN3D Stratos.")
                wrapMode: Text.WordWrap
                font: UM.Theme.getFont("medium")
                color: UM.Theme.getColor("text")
                renderType: Text.NativeRendering
            }

            Grid {
                columns: 1
                spacing: UM.Theme.getSize("wide_margin").height
                anchors.horizontalCenter: parent.horizontalCenter
                
                Column
                {
                    leftPadding: UM.Theme.getSize("default_margin").width
                    rightPadding: UM.Theme.getSize("default_margin").width
                    spacing: UM.Theme.getSize("default_margin").height

                    Image
                    {
                        id: image
                        source: UM.Theme.getImage("stratos_welcome")
                        MouseArea {
                            anchors.fill: parent
                            onClicked: {
                                Qt.openUrlExternally("http://www.bcn3d.com/stratos_tutorial")
                            }
                        }
                    }

                    Cura.IconWithText
                    {
                        id: iconWithText
                        width: image.width
                        anchors.horizontalCenter: image.horizontalCenter
                        source:  UM.Theme.getIcon("info-circled")
                        text: catalog.i18nc("@text", "6 minute video")
                        font: UM.Theme.getFont("default")
                        color: UM.Theme.getColor("text")
                    } 
                }
            }

            Label
            {
                id: experimentBeyond
                width: parent.width
                anchors.horizontalCenter: parent.horizontalCenter
                horizontalAlignment: Text.AlignHCenter
                text: catalog.i18nc("@text", 'Do you want to experiment beyond the standard mode?') +  "\n" + catalog.i18nc("@text", 'Learn how to configure your BCN3D Stratos printing parameters.') + ":"
                wrapMode: Text.WordWrap
                font: UM.Theme.getFont("medium")
                color: UM.Theme.getColor("text")
                renderType: Text.NativeRendering
            }
            Label
            {
                id: bottomLabel
                width: parent.width
                anchors.horizontalCenter: parent.horizontalCenter
                horizontalAlignment: Text.AlignHCenter
                text:
                {
                    var t1 = catalog.i18nc("@text", 'Basic parameters')
                    var t2 = catalog.i18nc("@text", 'Advanced parameters')
                    var t = " <a href='http://www.bcn3d.com/stratos_basic'>-" + t1 + "</a>           <a href='http://www.bcn3d.com/stratos_advanced'>-" + t2 +"</a>"
                    return t
                }
                textFormat: Text.RichText
                wrapMode: Text.WordWrap
                font: UM.Theme.getFont("medium")
                color: UM.Theme.getColor("text")
                linkColor: UM.Theme.getColor("text_link")
                onLinkActivated: Qt.openUrlExternally(link)
                renderType: Text.NativeRendering
            }       
        }
        
    }

    



    Cura.PrimaryButton
    {
        id: getStartedAplicationButton
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        text: catalog.i18nc("@button", "Next")
        onClicked: base.showNextPage()
    }
}
