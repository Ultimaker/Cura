// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.2
import QtQuick.Layouts 1.1
import QtQuick.Controls.Styles 1.1

import UM 1.0 as UM

Item 
{
    width: 250
    height: 250

    Slider 
    {
        width: 10
        height: 250
        anchors.right : parent.right
        orientation: Qt.Vertical
        minimumValue: 0;
        maximumValue: 100;

        value: 100;
        onValueChanged: UM.ActiveView.triggerAction("setLayer", value)

        style: UM.Theme.styles.slider;
    }
}
