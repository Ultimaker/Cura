// Copyright (c) 2018 Ultimaker B.V.
// Toolbox is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Dialogs 1.1
import QtQuick.Window 2.2
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4

// TODO: Switch to QtQuick.Controls 2.x and remove QtQuick.Controls.Styles

import UM 1.1 as UM

UM.Dialog
{
    title: catalog.i18nc("@title:window", "Plugin License Agreement")
    minimumWidth: UM.Theme.getSize("license_window_minimum").width
    minimumHeight: UM.Theme.getSize("license_window_minimum").height
    width: minimumWidth
    height: minimumHeight
    property var pluginName;
    property var licenseContent;
    property var pluginFileLocation;
    Item
    {
        anchors.fill: parent
        Label
        {
            id: licenseTitle
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            text: licenseDialog.pluginName + catalog.i18nc("@label", "This plugin contains a license.\nYou need to accept this license to install this plugin.\nDo you agree with the terms below?")
            wrapMode: Text.Wrap
            renderType: Text.NativeRendering
        }
        TextArea
        {
            id: licenseText
            anchors.top: licenseTitle.bottom
            anchors.bottom: parent.bottom
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.topMargin: UM.Theme.getSize("default_margin").height
            readOnly: true
            text: licenseDialog.licenseContent || ""
        }
    }
    rightButtons:
    [
        Button
        {
            id: acceptButton
            anchors.margins: UM.Theme.getSize("default_margin").width
            text: catalog.i18nc("@action:button", "Accept")
            onClicked:
            {
                licenseDialog.close();
                toolbox.install(licenseDialog.pluginFileLocation);
            }
        },
        Button
        {
            id: declineButton
            anchors.margins: UM.Theme.getSize("default_margin").width
            text: catalog.i18nc("@action:button", "Decline")
            onClicked:
            {
                licenseDialog.close();
            }
        }
    ]
}
