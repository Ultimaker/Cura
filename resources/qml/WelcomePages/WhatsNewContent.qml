// Copyright (c) 2021 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3

import UM 1.5 as UM
import Cura 1.1 as Cura


//
// This component contains the content for the "What's new in Ultimaker Cura" page of the welcome on-boarding process.
// Previously this was just the changelog, but now it will just have the larger stories, the changelog has its own page.
//
Item
{
    property var manager: CuraApplication.getWhatsNewPagesModel()

    UM.I18nCatalog { id: catalog; name: "cura" }

    UM.Label
    {
        id: titleLabel
        anchors.top: parent.top
        anchors.horizontalCenter: parent.horizontalCenter
        horizontalAlignment: Text.AlignHCenter
        text: catalog.i18nc("@label", "What's New")
        color: UM.Theme.getColor("primary_button")
        font: UM.Theme.getFont("huge")
    }

    Rectangle
    {
        anchors
        {
            top: titleLabel.bottom
            topMargin: UM.Theme.getSize("default_margin").width
            bottom: whatsNewDots.top
            bottomMargin: UM.Theme.getSize("narrow_margin").width
            left: parent.left
            right: parent.right
        }

        color: UM.Theme.getColor("viewport_overlay")

        StackLayout
        {
            id: whatsNewViewport

            anchors
            {
                top: parent.top
                horizontalCenter: parent.horizontalCenter
            }
            height: parent.height
            width: parent.width

            currentIndex: whatsNewDots.currentIndex

            Repeater
            {

                model: manager.subpageCount

                Rectangle
                {
                    Layout.alignment: Qt.AlignHCenter
                    color: UM.Theme.getColor("viewport_overlay")
                    width: whatsNewViewport.width
                    height: whatsNewViewport.height

                    AnimatedImage
                    {
                        id: subpageImage

                        anchors
                        {
                            top: parent.top
                            topMargin: UM.Theme.getSize("thick_margin").width
                            left: parent.left
                            leftMargin: UM.Theme.getSize("thick_margin").width
                            right: parent.right
                            rightMargin: UM.Theme.getSize("thick_margin").width
                        }
                        width: Math.round(parent.width - (UM.Theme.getSize("thick_margin").height * 2))
                        fillMode: Image.PreserveAspectFit
                        onStatusChanged: playing = (status == AnimatedImage.Ready)

                        source: manager.getSubpageImageSource(index)
                    }

                    Cura.ScrollableTextArea
                    {
                        id: subpageText

                        anchors
                        {
                            top: subpageImage.bottom
                            topMargin: UM.Theme.getSize("default_margin").height
                            bottom: parent.bottom
                            bottomMargin: UM.Theme.getSize("thin_margin").height
                            left: subpageImage.left
                            right: subpageImage.right
                        }

                        back_color: UM.Theme.getColor("viewport_overlay")
                        do_borders: false

                        textArea.wrapMode: TextEdit.Wrap
                        textArea.text: "<style>a:link { color: " + UM.Theme.getColor("text_link") + "; text-decoration: underline; }</style>" + manager.getSubpageText(index)
                        textArea.textFormat: Text.RichText
                        textArea.readOnly: true
                        textArea.font: UM.Theme.getFont("default")
                        textArea.onLinkActivated: Qt.openUrlExternally(link)
                        textArea.leftPadding: 0
                        textArea.rightPadding: 0
                    }
                }
            }
        }
    }

    PageIndicator
    {
        id: whatsNewDots

        currentIndex: whatsNewViewport.currentIndex
        count: whatsNewViewport.count
        interactive: true

        anchors
        {
            bottom: whatsNewNextButton.top
            bottomMargin: UM.Theme.getSize("wide_margin").height
            horizontalCenter: parent.horizontalCenter
        }

        delegate:
            Rectangle
            {
                width: UM.Theme.getSize("thin_margin").width
                height: UM.Theme.getSize("thin_margin").height

                radius: width / 2
                color:
                    index === whatsNewViewport.currentIndex ?
                    UM.Theme.getColor("primary") :
                    UM.Theme.getColor("secondary_button_shadow")
            }
    }

    Item
    {
        id: bottomSpacer
        anchors.bottom: whatsNewNextButton.top
        height: UM.Theme.getSize("default_margin").height / 2
        width: UM.Theme.getSize("default_margin").width / 2
    }

    Cura.TertiaryButton
    {
        id: whatsNewNextButton
        anchors.left: parent.left
        anchors.bottom: parent.bottom
        text: base.currentItem.next_page_button_text
        onClicked: base.showNextPage()
    }

    Cura.PrimaryButton
    {
        id: whatsNewSubpageButton
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        text: catalog.i18nc("@button", "Next")
        onClicked:
            whatsNewDots.currentIndex === (whatsNewDots.count - 1) ?
            base.showNextPage() :
            ++whatsNewDots.currentIndex
    }
}
