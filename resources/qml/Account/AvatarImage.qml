// Copyright (c) 2018 Ultimaker B.V.
import QtQuick 2.7
import QtQuick.Controls 2.1
import QtGraphicalEffects 1.0

import UM 1.4 as UM

Item
{
    id: avatar

    property var source
    property var fallbackSource: UM.Theme.getImage("avatar_default")
    property var outlineColor: UM.Theme.getColor("account_widget_ouline_active")

    Image
    {
        id: profileImage
        source: avatar.source ? avatar.source : UM.Theme.getImage("avatar_default")
        sourceSize: Qt.size(parent.width, parent.height)
        width: parent.width
        height: parent.height
        fillMode: Image.PreserveAspectCrop
        visible: false
    }

    UM.RecolorImage
    {
        id: profileImageMask
        source: UM.Theme.getIcon("circle_mask")
        sourceSize: Qt.size(parent.width, parent.height)
        width: parent.width
        height: parent.height
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
        width: parent.width
        height: parent.height
        color: avatar.outlineColor
    }
}