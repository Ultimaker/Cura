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
    id: licenseDialog
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

        UM.I18nCatalog{id: catalog; name: "cura"}


        Label
        {
            id: licenseTitle
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            text: licenseModel.title
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
            text: licenseModel.licenseText
        }
    }
    rightButtons:
    [
        Button
        {
            id: acceptButton
            anchors.margins: UM.Theme.getSize("default_margin").width
            text: catalog.i18nc("@action:button", "Accept")
            onClicked: handler.onLicenseAccepted
        },
        Button
        {
            id: declineButton
            anchors.margins: UM.Theme.getSize("default_margin").width
            text: catalog.i18nc("@action:button", "Decline")
            onClicked: handler.onLicenseDeclined
        }
    ]
}
