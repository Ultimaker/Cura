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
        anchors.topMargin: 40
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
        anchors.topMargin: 40
        anchors.bottomMargin: 40
        anchors.horizontalCenter: parent.horizontalCenter
        width: parent.width * 3 / 4

        border.color: "#dfdfdf"
        border.width: 1

        ScrollView
        {
            anchors.fill: parent
            anchors.margins: 1

            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

            TextArea
            {
                id: whatsNewTextArea
                text: catalog.i18nc("@text", "<p><b>Ultimaker Cura 4.0</b></p>

    <p>New features</p>

    <p><b>Brand new user interface.</b> Ultimaker Cura is a very powerful tool with many features to support users’ needs. In the new UI, we present these features in a better, more intuitive way based on the workflow of our users. The Marketplace and user account control have been integrated into the main interface to easily access material profiles and plugins. Within the UI, three stages are shown in the header to give a clear guidance of the flow. The stage menu is populated with collapsible panels that allow users to focus on the 3D view when needed, while still showing important information at the same time, such as slicing configuration and settings. Users can now easily go to the preview stage to examine the layer view after slicing the model, which previously was less obvious or hidden. The new UI also creates more distinction between recommended and custom mode. Novice users or users who are not interested in all the settings can easily prepare a file without diving into details. Expert users can use custom mode with a resizable settings panel to make more settings visible, and the set position will persist between sessions.</p>

    <p><b>Cloud printing.</b> Pair your Ultimaker printer with an Ultimaker account so you can send and monitor print jobs from outside your local network.</p>

    <p><b>Redesigned &quot;Add Printer&quot; dialog.</b> Updated one of the first dialogs a new user is presented with. The layout is loosely modeled on the layout of the Ultimaker 3/Ultimaker S5 &quot;Connect to Network&quot; dialog, and adds some instructions and intention to the dialog. Contributed by fieldOfView.</p>

    <p><b>Integrated backups.</b> Cura backups has been integrated into Ultimaker Cura and can be found in the 'extensions' menu. With this feature, users can backup their Ultimaker Cura configurations to the cloud.</p>
    ")
                textFormat: Text.RichText
                wrapMode: Text.WordWrap
                readOnly: true
                font: UM.Theme.getFont("default")
                renderType: Text.NativeRendering
            }
        }
    }

    Cura.PrimaryButton
    {
        id: getStartedButton
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.margins: 40
        text: catalog.i18nc("@button", "Next")
        width: UM.Theme.getSize("welcome_pages_button").width
        fixedWidthMode: true
        onClicked: base.showNextPage()
    }
}
