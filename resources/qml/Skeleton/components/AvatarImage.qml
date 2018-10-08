// Copyright (c) 2018 Ultimaker B.V.
import QtQuick 2.7
import QtQuick.Controls 2.1
import QtGraphicalEffects 1.0

import UM 1.4 as UM

Item
{
    id: avatar

    Image
    {
        id: profileImage
        source: UM.Theme.getImage("avatar_default")
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
}