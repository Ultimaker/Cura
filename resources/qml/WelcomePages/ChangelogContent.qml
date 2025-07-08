// Copyright (c) 2021 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.5 as UM
import Cura 1.1 as Cura


//
// This component contains the content for the "What's new in Ultimaker Cura" page of the welcome on-boarding process.
//
Item
{
    UM.I18nCatalog { id: catalog; name: "cura" }

    UM.Label
    {
        id: titleLabel
        anchors.top: parent.top
        anchors.horizontalCenter: parent.horizontalCenter
        horizontalAlignment: Text.AlignHCenter
        text: catalog.i18nc("@label", "Release Notes")
        color: UM.Theme.getColor("primary_button")
        font: UM.Theme.getFont("huge")
    }

    Cura.ScrollableTextArea
    {
        id: changelogTextArea

        anchors.top: titleLabel.bottom
        anchors.bottom: getStartedButton.top
        anchors.topMargin: UM.Theme.getSize("wide_margin").height
        anchors.bottomMargin: UM.Theme.getSize("wide_margin").height
        anchors.left: parent.left
        anchors.right: parent.right

        textArea.text: CuraApplication.getTextManager().getChangeLogText()
        textArea.textFormat: Text.RichText
        textArea.wrapMode: Text.WordWrap
        textArea.readOnly: true
        textArea.font: UM.Theme.getFont("default")
        textArea.onLinkActivated: Qt.openUrlExternally(link)
        textArea.rightPadding: 15
        textArea.leftPadding: 15
    }

    Cura.PrimaryButton
    {
        id: getStartedButton
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        text: base.currentItem.next_page_button_text
        onClicked: base.showNextPage()
    }
}
