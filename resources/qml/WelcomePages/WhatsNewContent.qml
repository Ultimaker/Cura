// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.3 as UM
import Cura 1.1 as Cura


//
// This component contains the content for the "What's new in Ultimaker Cura" page of the welcome on-boarding process.
//
Item
{
    UM.I18nCatalog { id: catalog; name: "cura" }

    Label
    {
        id: titleLabel
        anchors.top: parent.top
        anchors.topMargin: UM.Theme.getSize("welcome_pages_default_margin").height
        anchors.horizontalCenter: parent.horizontalCenter
        horizontalAlignment: Text.AlignHCenter
        text: catalog.i18nc("@label", "What's new in Ultimaker Cura")
        color: UM.Theme.getColor("primary_button")
        font: UM.Theme.getFont("large_bold")
        renderType: Text.NativeRendering
    }

    Rectangle
    {
        anchors.top: titleLabel.bottom
        anchors.bottom: getStartedButton.top
        anchors.topMargin: UM.Theme.getSize("welcome_pages_default_margin").height
        anchors.bottomMargin: UM.Theme.getSize("welcome_pages_default_margin").height
        anchors.horizontalCenter: parent.horizontalCenter
        width: (parent.width * 3 / 4) | 0

        border.color: "#dfdfdf"
        border.width: UM.Theme.getSize("default_lining").width

        ScrollView
        {
            anchors.fill: parent
            anchors.margins: UM.Theme.getSize("default_lining").width

            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

            TextArea
            {
                id: whatsNewTextArea
                text: CuraApplication.getTextManager().getChangeLogText()
                textFormat: Text.RichText
                wrapMode: Text.WordWrap
                readOnly: true
                font: UM.Theme.getFont("default")
                renderType: Text.NativeRendering
            }

            Component.onCompleted:
            {
                Scrollbar.vertical.position = 0;
            }
        }
    }

    Cura.PrimaryButton
    {
        id: getStartedButton
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.margins: UM.Theme.getSize("welcome_pages_default_margin").width
        text: catalog.i18nc("@button", "Next")
        width: UM.Theme.getSize("welcome_pages_button").width
        fixedWidthMode: true
        onClicked: base.showNextPage()
    }
}
