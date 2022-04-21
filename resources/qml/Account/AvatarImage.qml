// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.4 as UM

Item
{
    // This item shows the provided image while applying a round mask to it.
    // It also shows a round border around it. The color is defined by the outlineColor property.

    id: avatar

    property alias source: profileImage.source
    property alias outlineColor: profileImageOutline.color

    // This should be set to the color behind the image
    // It fills the space around a rectangular avatar to make the image under it look circular
    property alias maskColor: profileImageMask.color
    property bool hasAvatar: source != ""

    Rectangle
    {
        id: profileImageBackground
        anchors.fill: parent
        radius: width
        color: "white"
    }

    Image
    {
        id: profileImage
        anchors.fill: parent
        fillMode: Image.PreserveAspectCrop
        visible: hasAvatar
        mipmap: true
    }

    UM.ColorImage
    {
        // This image is a rectangle with a hole in the middle.
        // Since we don't have access to proper masking in QT6 yet this is used as a primitive masking replacement
        id: profileImageMask
        anchors.fill: parent
        source: UM.Theme.getIcon("CircleMask")
    }

    UM.ColorImage
    {
        // This creates the circle outline around the image
        id: profileImageOutline
        anchors.fill: parent
        anchors.margins: .25
        visible: hasAvatar
        source: UM.Theme.getIcon("CircleOutline")
        color: UM.Theme.getColor("account_widget_outline_active")
    }
}
