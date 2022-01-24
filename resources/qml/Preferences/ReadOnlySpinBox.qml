// Copyright (c) 2016 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.1
import QtQuick.Controls 1.1
import QtQuick.Dialogs 1.2

Item
{
    id: base

    property alias value: spinBox.value
    property alias minimumValue: spinBox.minimumValue
    property alias maximumValue: spinBox.maximumValue
    property alias stepSize: spinBox.stepSize
    property alias prefix: spinBox.prefix
    property alias suffix: spinBox.suffix
    property alias decimals: spinBox.decimals

    signal editingFinished();

    property bool readOnly: false

    width: spinBox.width
    height: spinBox.height

    SpinBox
    {
        id: spinBox

        enabled: !base.readOnly
        opacity: base.readOnly ? 0.5 : 1.0

        anchors.fill: parent

        onEditingFinished: base.editingFinished()
        Keys.onEnterPressed: spinBox.focus = false
        Keys.onReturnPressed: spinBox.focus = false
    }

    Label
    {
        visible: base.readOnly
        text: base.prefix + base.value.toFixed(spinBox.decimals) + base.suffix

        anchors.verticalCenter: parent.verticalCenter
        anchors.left: parent.left
        anchors.leftMargin: spinBox.__style ? spinBox.__style.padding.left : 0

        color: palette.buttonText
    }

    SystemPalette { id: palette }
}
