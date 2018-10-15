// Copyright (c) 2018 Ultimaker B.V.
import QtQuick 2.7
import QtQuick.Controls 2.1
import QtGraphicalEffects 1.0

import UM 1.4 as UM

Item
{
    // This item shows the provided image while applying a round mask to it.
    // It also shows a round border around it. The color is defined by the outlineColor property.

    id: avatar

    property alias source: profileImage.source
    property alias outlineColor: profileImageOutline.color

    Image
    {
        id: profileImage
        source: UM.Theme.getImage("avatar_default")
        anchors.fill: parent
        fillMode: Image.PreserveAspectCrop
        visible: false
    }

    UM.RecolorImage
    {
        id: profileImageMask
        source: UM.Theme.getIcon("circle_mask")
        sourceSize: Qt.size(parent.width, parent.height)
        anchors.fill: parent
        color: UM.Theme.getColor("topheader_background")
        visible: false
    }

    OpacityMask
    {
        anchors.fill: profileImage
        source: profileImage
        maskSource: profileImageMask
        cached: true
        invert: false
    }

    UM.RecolorImage
    {
        id: profileImageOutline
        source: UM.Theme.getIcon("circle_outline")
        sourceSize: Qt.size(parent.width, parent.height)
        anchors.fill: parent
        color: UM.Theme.getColor("account_widget_ouline_active")
    }
}