// Copyright (c) 2021 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3

import UM 1.3 as UM
import Cura 1.1 as Cura


//
// This component contains the content for the "What's new in Ultimaker Cura" page of the welcome on-boarding process.
// Previously this was just the changelog, but now it will just have the larger stories, the changelog has its own page.
//
Item
{
    property var manager: CuraApplication.getWhatsNewPagesModel()

    UM.I18nCatalog { id: catalog; name: "cura" }

    Label
    {
        id: titleLabel
        anchors.top: parent.top
        anchors.horizontalCenter: parent.horizontalCenter
        horizontalAlignment: Text.AlignHCenter
        text: catalog.i18nc("@label", "What's New")
        color: UM.Theme.getColor("primary_button")
        font: UM.Theme.getFont("huge")
        renderType: Text.NativeRendering
    }

    Item
    {
        id: topSpacer
        anchors.top: titleLabel.bottom
        height: UM.Theme.getSize("default_margin").height
        width: UM.Theme.getSize("default_margin").width
    }

    Rectangle
    {
        anchors
        {
            top: topSpacer.bottom
            bottom: whatsNewDots.top
            left: parent.left
            right: parent.right
            margins: UM.Theme.getSize("default_margin").width * 2
        }

        color: UM.Theme.getColor("viewport_overlay")

        StackLayout
        {
            id: whatsNewViewport

            anchors
            {
                top: parent.top
                topMargin: UM.Theme.getSize("default_margin").width
                horizontalCenter: parent.horizontalCenter
            }
            height: parent.height
            width: parent.width

            currentIndex: whatsNewDots.currentIndex

            Repeater
            {
                anchors
                {
                    top: parent.top
                    topMargin: UM.Theme.getSize("default_margin").width / 2
                    horizontalCenter: parent.horizontalCenter
                }

                model: manager.subpageCount

                Rectangle
                {
                    Layout.alignment: Qt.AlignHCenter
                    color: UM.Theme.getColor("viewport_overlay")

                    Image
                    {
                        id: subpageImage

                        anchors
                        {
                            horizontalCenter: parent.horizontalCenter
                            top: parent.top
                            topMargin: UM.Theme.getSize("default_margin").width
                        }
                        width: Math.round(parent.width - (UM.Theme.getSize("default_margin").width * 2))
                        height: Math.round((parent.height - UM.Theme.getSize("default_margin").height) * 0.75)
                        fillMode: Image.PreserveAspectFit

                        source: manager.getSubpageImageSource(index)
                    }

                    Cura.ScrollableTextArea
                    {
                        id: subpageText

                        anchors
                        {
                            top: subpageImage.bottom
                            bottom: parent.bottom
                            horizontalCenter: parent.horizontalCenter
                        }
                        width: Math.round(parent.width - (UM.Theme.getSize("default_margin").width * 2))

                        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

                        back_color: UM.Theme.getColor("viewport_overlay")
                        do_borders: false

                        textArea.wrapMode: TextEdit.Wrap
                        textArea.text: manager.getSubpageText(index)
                        textArea.textFormat: Text.RichText
                        textArea.readOnly: true
                        textArea.font: UM.Theme.getFont("medium")
                        textArea.onLinkActivated: Qt.openUrlExternally(link)
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
            bottom: bottomSpacer.top
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
