// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3


Item
{
    id: base

    property int totalSteps: 10
    property int currentStep: 6
    property int radius: 2

    Rectangle
    {
        id: background
        anchors.fill: parent
        color: "#f0f0f0"
        radius: base.radius
    }

    Rectangle
    {
        id: progress
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: (currentStep + 1) * 1.0 / totalSteps * background.width
        color: "#3282ff"
        radius: base.radius
    }
}
