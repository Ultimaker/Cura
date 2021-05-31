// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtGraphicalEffects 1.0

import UM 1.4 as UM

Item
{
    // This item shows the provided image while applying a round mask to it.
    // It also shows a round border around it. The color is defined by the outlineColor property.

    id: avatar

    property alias source: profileImage.source
    property alias outlineColor: profileImageOutline.color
    property bool hasAvatar: source != ""

    Image
    {
        id: profileImage
        anchors.fill: parent
        fillMode: Image.PreserveAspectCrop
        visible: false
        mipmap: true
    }

    Rectangle
    {
        id: profileImageMask
        anchors.fill: parent
        radius: width
        color: hasAvatar ? "white" : "transparent"
    }

    OpacityMask
    {
        anchors.fill: parent
        source: profileImage
        maskSource: profileImageMask
        visible: hasAvatar
        cached: true
    }

    UM.RecolorImage
    {
        id: profileImageOutline
        anchors.centerIn: parent
        // Make it a bit bigger than it has to, otherwise it sometimes shows a white border.
        width: parent.width + 2
        height: parent.height + 2
        visible: hasAvatar
        source: UM.Theme.getIcon("circle_outline")
        sourceSize: Qt.size(parent.width, parent.height)
        color: UM.Theme.getColor("account_widget_outline_active")
    }
}
